import os
import math
import pickle
import concurrent.futures
import numpy as np
import pandas as pd
import xarray as xr

class IncoisDatasetResolver:
    # Remote OPENDAP Endpoints
    WW3_URL = "https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_20260825.nc"
    CURRENTS_URL = "https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_20260824.nc"
    
    # Cache Directory
    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
    
    @classmethod
    def get_cache_paths(cls, lat: float, lon: float, day: int):
        ww3_dir = os.path.join(cls.CACHE_DIR, "ww3")
        currents_dir = os.path.join(cls.CACHE_DIR, "currents")
        os.makedirs(ww3_dir, exist_ok=True)
        os.makedirs(currents_dir, exist_ok=True)
        
        # Round coordinate to 3 decimals to avoid cache fragmentation
        lat_r = round(lat, 3)
        lon_r = round(lon, 3)
        
        key = f"lat_{lat_r}_lon_{lon_r}_day_{day}.pkl"
        return os.path.join(ww3_dir, key), os.path.join(currents_dir, key)

    @classmethod
    def resolve_latest_forecast(cls, lat: float, lon: float, day: int):
        """
        Dynamically queries the remote WW3 and Currents NetCDF datasets using OPENDAP.
        Slices coordinates spatially and temporally for the target day (1, 2, or 3).
        Applies caching, quality control, unit conversions, and vector derivations.
        Includes a strict 4.0-second timeout to fall back immediately if INCOIS hangs.
        """
        ww3_cache_file, curr_cache_file = cls.get_cache_paths(lat, lon, day)
        
        # 1. Attempt to load from cache
        if os.path.exists(ww3_cache_file) and os.path.exists(curr_cache_file):
            try:
                with open(ww3_cache_file, "rb") as f:
                    ww3_data = pickle.load(f)
                with open(curr_cache_file, "rb") as f:
                    curr_data = pickle.load(f)
                return ww3_data, curr_data
            except Exception as e:
                # Fallback to remote fetching if cache is corrupted
                pass

        # 2. Run remote fetch with a 4.0-second thread timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(cls._fetch_remote, lat, lon, day, ww3_cache_file, curr_cache_file)
            try:
                return future.result(timeout=4.0)
            except concurrent.futures.TimeoutError:
                raise TimeoutError("INCOIS OPENDAP remote server timed out.")

    @classmethod
    def _fetch_remote(cls, lat: float, lon: float, day: int, ww3_cache_file: str, curr_cache_file: str):
        try:
            ds_ww3 = xr.open_dataset(cls.WW3_URL)
            ds_curr = xr.open_dataset(cls.CURRENTS_URL)
            
            # Spatial slicing using nearest neighbor
            ww3_slice = ds_ww3.sel(IOYAXIS=lat, IOXAXIS=lon, method="nearest")
            curr_slice = ds_curr.sel(LAT=lat, LON=lon, DEPTH1_1=0.0, method="nearest")
            
            # Slices are 1D along time dimension (TIME for WW3, TAXIS for currents)
            start_idx = (day - 1) * 8
            
            # Fetch from start_idx - 2 to support the 6-hour lookback
            target_indices_ww3 = list(range(max(0, start_idx - 2), min(len(ds_ww3.TIME), start_idx + 8)))
            ww3_subset = ww3_slice.isel(TIME=target_indices_ww3)
            
            # Normalize and read WW3 parameters
            times_ww3 = [str(t) for t in ww3_subset.TIME.values]
            hs = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.HS.values]
            stp = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.STP.values]
            spr_raw = [float(v) if not np.isnan(v) else 30.0 for v in ww3_subset.SPR.values]
            spr = []
            for v in spr_raw:
                rad = math.radians(v)
                s_s = math.sqrt(2.0 * (1.0 - math.cos(rad)))
                spr.append(s_s)
            mwd = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.MWD.values]
            t02 = [float(v) if not np.isnan(v) else 6.0 for v in ww3_subset.T02.values]
            u_wnd = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.UWND.values]
            v_wnd = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.VWND.values]
            
            # PHS00 is the wind-sea wave height variable
            hsea = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.PHS00.values]
            
            offset = 2 if start_idx - 2 >= 0 else 0
            
            ww3_records = []
            curr_records = []
            
            for k in range(8):
                idx = offset + k
                lookback_idx = idx - 2 if idx - 2 >= 0 else idx
                
                # Derive wind variables: speed = sqrt(U^2 + V^2) * 3.6 (m/s to km/h)
                wind_speed_kmh = math.sqrt(u_wnd[idx]**2 + v_wnd[idx]**2) * 3.6
                
                # Derive wind direction (using standard meteorological convention: direction from which wind blows)
                wind_dir_rad = math.atan2(u_wnd[idx], v_wnd[idx])
                wind_dir_deg = (math.degrees(wind_dir_rad) + 180) % 360
                
                ww3_step = {
                    "timestamp": times_ww3[idx],
                    "hs": hs[idx],
                    "stp": stp[idx],
                    "spr": spr[idx],
                    "mwd": mwd[idx],
                    "t02": t02[idx],
                    "wind_speed_kmh": wind_speed_kmh,
                    "wind_direction_deg": wind_dir_deg,
                    "hsea_initial": hsea[lookback_idx],
                    "hsea_final": hsea[idx]
                }
                ww3_records.append(ww3_step)
                
                # Temporal alignment: select the closest timestamp in currents dataset
                target_timestamp = pd.to_datetime(times_ww3[idx])
                curr_step = curr_slice.sel(TAXIS=target_timestamp, method="nearest")
                
                u_curr = float(curr_step.U.values) if not np.isnan(curr_step.U.values) else 0.0
                v_curr = float(curr_step.V.values) if not np.isnan(curr_step.V.values) else 0.0
                
                # Derive current speed: speed = sqrt(U^2 + V^2)
                curr_speed_ms = math.sqrt(u_curr**2 + v_curr**2)
                
                # Derive current direction (using oceanographic convention: direction towards which current flows)
                curr_dir_rad = math.atan2(u_curr, v_curr)
                curr_dir_deg = math.degrees(curr_dir_rad)
                curr_dir = curr_dir_deg if curr_dir_deg >= 0 else 360.0 + curr_dir_deg
                
                curr_step_record = {
                    "timestamp_ww3": times_ww3[idx],
                    "timestamp_curr": str(curr_step.TAXIS.values),
                    "u_m_s": u_curr,
                    "v_m_s": v_curr,
                    "speed_m_s": curr_speed_ms,
                    "direction_deg": curr_dir
                }
                curr_records.append(curr_step_record)
                
            # 3. Save to cache files
            with open(ww3_cache_file, "wb") as f:
                pickle.dump(ww3_records, f)
            with open(curr_cache_file, "wb") as f:
                pickle.dump(curr_records, f)
                
            return ww3_records, curr_records
            
        except Exception as e:
            # Propagate error so endpoints can trigger fallbacks
            raise RuntimeError(f"INCOIS Remote fetch error: {e}")
