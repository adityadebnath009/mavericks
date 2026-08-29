import os
import math
import pickle
import concurrent.futures
import numpy as np
import pandas as pd
import xarray as xr
import time

class IncoisDatasetResolver:
    # Cache Directory
    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
    
    @classmethod
    def _get_latest_catalog_dataset(cls, catalog_url: str, prefix: str) -> str:
        """
        Discover the latest published INCOIS dataset from a THREDDS catalog.

        The catalog is the source of truth. We do NOT assume today's date
        or construct filenames manually.
        """
        import requests
        import xml.etree.ElementTree as ET
        from datetime import datetime

        response = requests.get(catalog_url, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        namespace = {
            "thredds": "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
        }

        candidates = []

        for dataset in root.findall(".//thredds:dataset", namespace):
            name = dataset.attrib.get("name", "")
            url_path = dataset.attrib.get("urlPath", "")

            if not name.startswith(prefix):
                continue

            if not name.endswith(".nc"):
                continue

            # Read THREDDS modification date
            modified = None

            for date_node in dataset.findall("thredds:date", namespace):
                if date_node.attrib.get("type") == "modified":
                    try:
                        modified = datetime.fromisoformat(
                            date_node.text.strip().replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

            if not url_path:
                continue

            candidates.append(
                {
                    "name": name,
                    "url_path": url_path,
                    "modified": modified,
                }
            )

        if not candidates:
            raise RuntimeError(
                f"No {prefix} NetCDF datasets found in {catalog_url}"
            )

        # Prefer catalog modification timestamp.
        # If timestamps are unavailable, fall back to filename ordering.
        candidates.sort(
            key=lambda x: (
                x["modified"] is not None,
                x["modified"] or datetime.min,
                x["name"],
            ),
            reverse=True,
        )

        latest = candidates[0]

        return (
            "https://www.incois.gov.in/thredds/dodsC/"
            + latest["url_path"]
        )

    _url_cache = {}
    _url_cache_time = {}

    @classmethod
    def get_ww3_url(cls):
        now = time.time()
        if "ww3" in cls._url_cache and now - cls._url_cache_time.get("ww3", 0) < 600:
            return cls._url_cache["ww3"]
            
        url = cls._get_latest_catalog_dataset(
            "https://www.incois.gov.in/thredds/catalog/osf/ww3/catalog.xml",
            "rsmc_nio_ww3_",
        )
        cls._url_cache["ww3"] = url
        cls._url_cache_time["ww3"] = now
        return url

    @classmethod
    def get_currents_url(cls):
        now = time.time()
        if "currents" in cls._url_cache and now - cls._url_cache_time.get("currents", 0) < 600:
            return cls._url_cache["currents"]
            
        url = cls._get_latest_catalog_dataset(
            "https://www.incois.gov.in/thredds/catalog/osf/currents/catalog.xml",
            "CURRENTS_IO_",
        )
        cls._url_cache["currents"] = url
        cls._url_cache_time["currents"] = now
        return url
    
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

    _ds_cache = {}
    _ds_cache_time = {}

    @classmethod
    def _get_dataset(cls, url: str):
        now = time.time()
        if url in cls._ds_cache and now - cls._ds_cache_time.get(url, 0) < 300:
            return cls._ds_cache[url]
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ds = xr.open_dataset(url, engine="pydap")
        cls._ds_cache[url] = ds
        cls._ds_cache_time[url] = now
        return ds

    @classmethod
    def _fetch_remote(cls, lat: float, lon: float, day: int, ww3_cache_file: str, curr_cache_file: str):
        try:
            # Using cached dataset connections to avoid repeated OPeNDAP metadata handshakes
            ds_ww3 = cls._get_dataset(cls.get_ww3_url())
            ds_curr = cls._get_dataset(cls.get_currents_url())
            
            # Spatial slicing using nearest neighbor
            ww3_slice = ds_ww3.sel(lat=lat, lon=lon, method="nearest")
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
            mwd = [float(v) if not np.isnan(v) else None for v in ww3_subset.MWD.values]
            t02 = [float(v) if not np.isnan(v) else None for v in ww3_subset.T02.values]
            u_wnd = [float(v) if not np.isnan(v) else None for v in ww3_subset.UWND.values]
            v_wnd = [float(v) if not np.isnan(v) else None for v in ww3_subset.VWND.values]
            
            # PHS00 is the wind-sea wave height variable
            hsea = [float(v) if not np.isnan(v) else None for v in ww3_subset.PHS00.values]
            
            offset = 2 if start_idx - 2 >= 0 else 0
            
            ww3_records = []
            curr_records = []
            
            for k in range(8):
                idx = offset + k
                lookback_idx = idx - 2 if idx - 2 >= 0 else idx
                
                u_val = u_wnd[idx]
                v_val = v_wnd[idx]
                
                if u_val is not None and v_val is not None:
                    # Derive wind variables: speed = sqrt(U^2 + V^2) * 3.6 (m/s to km/h)
                    wind_speed_kmh = math.sqrt(u_val**2 + v_val**2) * 3.6
                    # Derive wind direction (meteorological convention)
                    wind_dir_rad = math.atan2(u_val, v_val)
                    wind_dir_deg = (math.degrees(wind_dir_rad) + 180) % 360
                else:
                    wind_speed_kmh = None
                    wind_dir_deg = None
                
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
                
                u_curr = float(curr_step.U.values) if not np.isnan(curr_step.U.values) else None
                v_curr = float(curr_step.V.values) if not np.isnan(curr_step.V.values) else None
                
                if u_curr is not None and v_curr is not None:
                    # Derive current speed: speed = sqrt(U^2 + V^2)
                    curr_speed_ms = math.sqrt(u_curr**2 + v_curr**2)
                    # Derive current direction (oceanographic convention)
                    curr_dir_rad = math.atan2(u_curr, v_curr)
                    curr_dir_deg = math.degrees(curr_dir_rad)
                    curr_dir = curr_dir_deg if curr_dir_deg >= 0 else 360.0 + curr_dir_deg
                else:
                    curr_speed_ms = None
                    curr_dir = None
                
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

    @classmethod
    def resolve_vector_grid(cls, day: int = 1) -> dict:
        """
        Retrieves a 0.5-degree gridded vector field of Wind and Currents over the Indian EEZ.
        Caches the grid locally to prevent slow MapLibre rendering.
        """
        grid_cache = os.path.join(cls.CACHE_DIR, f"vector_grid_day_{day}.json")
        now_ts = time.time()
        
        # Cache for 6 hours
        if os.path.exists(grid_cache):
            if now_ts - os.path.getmtime(grid_cache) < 6 * 3600:
                try:
                    import json
                    with open(grid_cache, "r") as f:
                        return json.load(f)
                except:
                    pass

        try:
            import json
            import numpy as np
            import xarray as xr
            import math
            import pandas as pd
            
            ds_ww3 = cls._get_dataset(cls.get_ww3_url())
            ds_curr = cls._get_dataset(cls.get_currents_url())
            
            start_idx = (day - 1) * 8
            time_idx = min(start_idx + 4, len(ds_ww3.TIME) - 1)
            target_timestamp = ds_ww3.TIME.values[time_idx]
            
            # Subset domains roughly over Indian EEZ [Lat 5 to 25, Lon 65 to 95]
            ww3_slice = ds_ww3.sel(lat=slice(5, 25), lon=slice(65, 95)).isel(TIME=time_idx).coarsen(lat=2, lon=2, boundary="trim").mean()
            curr_slice = ds_curr.sel(LAT=slice(5, 25), LON=slice(65, 95), DEPTH1_1=0.0).sel(TAXIS=target_timestamp, method="nearest").coarsen(LAT=2, LON=2, boundary="trim").mean()
            
            wind_vectors = []
            lon_grid, lat_grid = np.meshgrid(ww3_slice.lon.values, ww3_slice.lat.values)
            for lat_val, lon_val, u, v in zip(
                lat_grid.ravel(),
                lon_grid.ravel(),
                ww3_slice.UWND.values.ravel(),
                ww3_slice.VWND.values.ravel()
            ):
                if not np.isnan(u) and not np.isnan(v):
                    speed = math.sqrt(u**2 + v**2) * 3.6
                    deg = (math.degrees(math.atan2(u, v)) + 180) % 360
                    wind_vectors.append({
                        "lat": round(float(lat_val), 2),
                        "lon": round(float(lon_val), 2),
                        "u": round(float(u), 2),
                        "v": round(float(v), 2),
                        "speed_kmh": round(speed, 1),
                        "direction_deg": round(deg, 1)
                    })
                    
            curr_vectors = []
            lon_grid_c, lat_grid_c = np.meshgrid(curr_slice.LON.values, curr_slice.LAT.values)
            for lat_val, lon_val, u, v in zip(
                lat_grid_c.ravel(),
                lon_grid_c.ravel(),
                curr_slice.U.values.ravel(),
                curr_slice.V.values.ravel()
            ):
                if not np.isnan(u) and not np.isnan(v):
                    speed = math.sqrt(u**2 + v**2)
                    deg = math.degrees(math.atan2(u, v))
                    deg = deg if deg >= 0 else 360.0 + deg
                    curr_vectors.append({
                        "lat": round(float(lat_val), 2),
                        "lon": round(float(lon_val), 2),
                        "u": round(float(u), 3),
                        "v": round(float(v), 3),
                        "speed_ms": round(speed, 2),
                        "direction_deg": round(deg, 1)
                    })
                    
            grid_data = {
                "wind": wind_vectors,
                "current": curr_vectors,
                "timestamp": str(target_timestamp)
            }
            
            with open(grid_cache, "w") as f:
                json.dump(grid_data, f)
                
            return grid_data
        except Exception:
            import logging
            logging.exception("Failed to generate vector grid")
            raise
