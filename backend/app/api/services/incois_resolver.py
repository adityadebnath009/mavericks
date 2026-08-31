import os
import time
import math
import pickle
import warnings
import collections
import threading
import concurrent.futures
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np
import xarray as xr
import xml.etree.ElementTree as ET

from app.core.exceptions import DataUnavailableError

@dataclass
class ForecastResult:
    records: List[Dict[str, Any]]
    provenance: Dict[str, Any]

class IncoisDatasetResolver:
    """Resolve the latest INCOIS WW3/current datasets and expose exact forecast slices."""

    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
    _url_cache = {}
    _url_cache_time = {}
    
    # 60-second memory cache for P0.7
    _memory_cache = {}
    _memory_cache_time = {}
    
    # Per-key locking for P0.5
    _locks = collections.defaultdict(threading.Lock)

    @classmethod
    def _get_latest_catalog_dataset(cls, catalog_url: str, prefix: str) -> str:
        import requests
        response = requests.get(catalog_url, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        namespace = {"thredds": "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"}
        candidates = []

        for dataset in root.findall(".//thredds:dataset", namespace):
            name = dataset.attrib.get("name", "")
            if name.startswith(prefix) and name.endswith(".nc"):
                access = dataset.find("thredds:access[@serviceName='opendap']", namespace)
                if access is not None:
                    url_path = access.attrib.get("urlPath")
                    if url_path:
                        base = catalog_url.split("/thredds/")[0]
                        dods_url = f"{base}/thredds/dodsC/{url_path}"
                        candidates.append((name, dods_url))

        if not candidates:
            raise RuntimeError(f"No valid {prefix} OPeNDAP dataset found in catalog.")
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    @classmethod
    def get_ww3_url(cls) -> str:
        url = "https://incois.gov.in/thredds/catalog/OOS/INCOIS_WW3/catalog.xml"
        now = time.time()
        if url in cls._url_cache and now - cls._url_cache_time[url] < 3600:
            return cls._url_cache[url]
        latest = cls._get_latest_catalog_dataset(url, "ww3_")
        cls._url_cache[url] = latest
        cls._url_cache_time[url] = now
        return latest

    @classmethod
    def get_currents_url(cls) -> str:
        url = "https://incois.gov.in/thredds/catalog/OOS/Currents/catalog.xml"
        now = time.time()
        if url in cls._url_cache and now - cls._url_cache_time[url] < 3600:
            return cls._url_cache[url]
        latest = cls._get_latest_catalog_dataset(url, "currents_")
        cls._url_cache[url] = latest
        cls._url_cache_time[url] = now
        return latest
        
    @classmethod
    def _extract_forecast_cycle(cls, url: str) -> str:
        # Expected format: .../ww3_YYYYMMDD_HH.nc
        basename = url.split("/")[-1]
        return basename.replace(".nc", "")

    @classmethod
    def get_cache_paths(cls, native_lat: float, native_lon: float, day: int, forecast_cycle: str):
        ww3_dir = os.path.join(cls.CACHE_DIR, "ww3")
        currents_dir = os.path.join(cls.CACHE_DIR, "currents")
        os.makedirs(ww3_dir, exist_ok=True)
        os.makedirs(currents_dir, exist_ok=True)
        key = f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_{forecast_cycle}.pkl"
        return os.path.join(ww3_dir, key), os.path.join(currents_dir, key)

    @classmethod
    def resolve_latest_forecast(cls, lat: float, lon: float, day: int) -> Tuple[ForecastResult, ForecastResult]:
        # P0.1 Native grid coordinate (deterministic alignment to 0.1 deg WW3 grid)
        native_lat = round(lat, 1)
        native_lon = round(lon, 1)
        
        # P0.2 Forecast cycle identity (determined instantly from cached URL metadata)
        ww3_url = cls.get_ww3_url()
        curr_url = cls.get_currents_url()
        ww3_cycle = cls._extract_forecast_cycle(ww3_url)
        curr_cycle = cls._extract_forecast_cycle(curr_url)
        
        # Memory Cache Check (P0.7) - Bounded to 60 seconds
        mem_key = f"{native_lat}_{native_lon}_{day}_{ww3_cycle}_{curr_cycle}"
        now = time.time()
        if mem_key in cls._memory_cache and now - cls._memory_cache_time.get(mem_key, 0) < 60:
            cached_data = cls._memory_cache[mem_key]
            ww3_result = ForecastResult(records=cached_data["ww3"], provenance=cached_data["ww3_prov"])
            curr_result = ForecastResult(records=cached_data["curr"], provenance=cached_data["curr_prov"])
            return ww3_result, curr_result

        ww3_cache_file, curr_cache_file = cls.get_cache_paths(native_lat, native_lon, day, f"{ww3_cycle}_{curr_cycle}")

        # P0.2 & P0.8 Disk Cache Read with strict 24h TTL and Corruption Recovery
        def load_cache_file(path: str, source: str, cycle: str):
            if os.path.exists(path):
                mtime = os.path.getmtime(path)
                cache_age = now - mtime
                if cache_age < 24 * 3600:
                    try:
                        with open(path, "rb") as f:
                            payload = pickle.load(f)
                            
                        # Validate structure and cycle
                        if isinstance(payload, dict) and "data" in payload and "metadata" in payload:
                            if payload["metadata"]["forecast_cycle"] == cycle:
                                return payload["data"], {
                                    "source": source,
                                    "cache_hit": True,
                                    "cache_age_seconds": int(cache_age),
                                    "forecast_cycle": payload["metadata"]["forecast_cycle"],
                                    "forecast_day": day
                                }
                    except (pickle.UnpicklingError, EOFError, OSError, KeyError) as e:
                        try: os.remove(path)
                        except OSError: pass # Safely quarantine
            return None, None

        # P0.5 Per-Key Lock
        lock = cls._locks[mem_key]
        with lock:
            # Double check if cache was written while we waited for the lock
            ww3_data, ww3_prov = load_cache_file(ww3_cache_file, "INCOIS_WW3", ww3_cycle)
            curr_data, curr_prov = load_cache_file(curr_cache_file, "INCOIS_Currents", curr_cycle)

            if ww3_data is not None and curr_data is not None:
                # Store in 60s memory cache
                cls._memory_cache[mem_key] = {"ww3": ww3_data, "ww3_prov": ww3_prov, "curr": curr_data, "curr_prov": curr_prov}
                cls._memory_cache_time[mem_key] = now
                return ForecastResult(ww3_data, ww3_prov), ForecastResult(curr_data, curr_prov)

            # P0.5 Cache Miss -> Remote Fetch
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(cls._fetch_remote, native_lat, native_lon, day, ww3_url, curr_url)
                    ww3_records, curr_records = future.result(timeout=15.0)
            except concurrent.futures.TimeoutError:
                raise TimeoutError("INCOIS OPENDAP remote server timed out.")
            except DataUnavailableError:
                raise
            except Exception as e:
                raise RuntimeError(f"INCOIS Remote fetch error: {e}") from e

            # Atomic Write (P0.4)
            def write_atomic(path: str, data: list, cycle: str):
                tmp_path = path + ".tmp"
                payload = {
                    "data": data,
                    "metadata": {
                        "cached_at": now,
                        "forecast_cycle": cycle
                    }
                }
                with open(tmp_path, "wb") as f:
                    pickle.dump(payload, f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)

            write_atomic(ww3_cache_file, ww3_records, ww3_cycle)
            write_atomic(curr_cache_file, curr_records, curr_cycle)

            ww3_prov = {
                "source": "INCOIS_WW3",
                "cache_hit": False,
                "cache_age_seconds": 0,
                "forecast_cycle": ww3_cycle,
                "forecast_day": day
            }
            curr_prov = {
                "source": "INCOIS_Currents",
                "cache_hit": False,
                "cache_age_seconds": 0,
                "forecast_cycle": curr_cycle,
                "forecast_day": day
            }

            # Update memory cache
            cls._memory_cache[mem_key] = {"ww3": ww3_records, "ww3_prov": ww3_prov, "curr": curr_records, "curr_prov": curr_prov}
            cls._memory_cache_time[mem_key] = now

            return ForecastResult(ww3_records, ww3_prov), ForecastResult(curr_records, curr_prov)

    @classmethod
    def _fetch_remote(cls, lat: float, lon: float, day: int, ww3_url: str, curr_url: str):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ds_ww3 = xr.open_dataset(ww3_url, engine="pydap")
            ds_curr = xr.open_dataset(curr_url, engine="pydap")

        ww3_slice = ds_ww3.sel(lat=lat, lon=lon, method="nearest")
        curr_slice = ds_curr.sel(LAT=lat, LON=lon, DEPTH1_1=0.0, method="nearest")

        start_idx = (day - 1) * 8
        target_indices = list(range(max(0, start_idx - 2), min(len(ds_ww3.TIME), start_idx + 8)))
        ww3_subset = ww3_slice.isel(TIME=target_indices)

        times_ww3 = [str(t) for t in ww3_subset.TIME.values]
        
        # P0.3 Safe extractor mapping NaN to DataUnavailableError
        def extract_safe(arr):
            res = []
            for v in arr:
                val = float(v)
                if np.isnan(val):
                    res.append(None)
                else:
                    res.append(val)
            return res

        hs = extract_safe(ww3_subset.HS.values)
        stp = extract_safe(ww3_subset.STP.values)
        spr_raw = extract_safe(ww3_subset.SPR.values)
        
        spr = []
        for v in spr_raw:
            if v is not None:
                spr.append(math.sqrt(2.0 * (1.0 - math.cos(math.radians(v)))))
            else:
                spr.append(None)
                
        mwd = extract_safe(ww3_subset.MWD.values)
        t02 = extract_safe(ww3_subset.T02.values)
        u_wnd = extract_safe(ww3_subset.UWND.values)
        v_wnd = extract_safe(ww3_subset.VWND.values)
        hsea = extract_safe(ww3_subset.PHS00.values)

        offset = 2 if start_idx - 2 >= 0 else 0
        ww3_records = []
        curr_records = []

        for k in range(8):
            idx = offset + k
            lookback_idx = idx - 2 if idx - 2 >= 0 else idx
            
            # P0.3 Strict Data Availability Check for Required Variables
            # hs, stp, spr, hsea_i, hsea_f are REQUIRED to calculate BSI
            if (hs[idx] is None or stp[idx] is None or spr[idx] is None or 
                hsea[lookback_idx] is None or hsea[idx] is None):
                raise DataUnavailableError("Missing required WW3 official data parameters (NaN detected). Cannot hallucinate fallback values.")

            u_val, v_val = u_wnd[idx], v_wnd[idx]
            if u_val is not None and v_val is not None:
                wind_speed_kmh = math.sqrt(u_val ** 2 + v_val ** 2) * 3.6
                wind_dir_deg = (math.degrees(math.atan2(u_val, v_val)) + 180) % 360
            else:
                wind_speed_kmh = None
                wind_dir_deg = None

            ww3_records.append({
                "timestamp": times_ww3[idx],
                "hs": hs[idx],
                "stp": stp[idx],
                "spr": spr[idx],
                "mwd": mwd[idx],
                "t02": t02[idx],
                "wind_speed_kmh": wind_speed_kmh,
                "wind_direction_deg": wind_dir_deg,
                "hsea_initial": hsea[lookback_idx],
                "hsea_final": hsea[idx],
            })

            target_timestamp = pd.to_datetime(times_ww3[idx])
            curr_step = curr_slice.sel(TAXIS=target_timestamp, method="nearest")
            u_curr = float(curr_step.U.values) if not np.isnan(curr_step.U.values) else None
            v_curr = float(curr_step.V.values) if not np.isnan(curr_step.V.values) else None

            if u_curr is not None and v_curr is not None:
                curr_speed_ms = math.sqrt(u_curr ** 2 + v_curr ** 2)
                curr_dir = math.degrees(math.atan2(u_curr, v_curr)) % 360
            else:
                curr_speed_ms = None
                curr_dir = None

            curr_records.append({
                "timestamp_ww3": times_ww3[idx],
                "timestamp_curr": str(curr_step.TAXIS.values),
                "u_m_s": u_curr,
                "v_m_s": v_curr,
                "speed_m_s": curr_speed_ms,
                "direction_deg": curr_dir,
            })

        return ww3_records, curr_records

    @classmethod
    def resolve_vector_grid(cls, day: int = 1, hour: int = 12) -> dict:
        """Return the wind/current vector field for the exact requested 3-hour forecast step."""
        valid_hours = {0, 3, 6, 9, 12, 15, 18, 21}
        if day not in {1, 2, 3}:
            raise ValueError("day must be 1, 2, or 3")
        if hour not in valid_hours:
            raise ValueError("hour must be one of 0, 3, 6, 9, 12, 15, 18, or 21")

        grid_cache = os.path.join(cls.CACHE_DIR, f"vector_grid_d{day}_h{hour}.json")
        if os.path.exists(grid_cache) and time.time() - os.path.getmtime(grid_cache) < 6 * 3600:
            import json
            with open(grid_cache, "r", encoding="utf-8") as f:
                return json.load(f)

        try:
            import json
            # Temporarily cache xarray Datasets for the vector grid function to speed it up if called repeatedly
            def get_ds(url):
                now = time.time()
                if url in cls._url_cache and now - cls._url_cache_time.get(url, 0) < 300:
                    pass # We do not memory cache the heavy datasets here anymore to save RAM
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    return xr.open_dataset(url, engine="pydap")

            ds_ww3 = get_ds(cls.get_ww3_url())
            ds_curr = get_ds(cls.get_currents_url())

            # WW3 is published on the 3-hour forecast cadence used by the UI.
            # Resolve the dataset's actual timestamp first, then select by timestamp.
            target_index = (day - 1) * 8 + (hour // 3)
            if target_index >= len(ds_ww3.TIME):
                raise IndexError(f"Requested forecast step is outside WW3 TIME dimension: day={day}, hour={hour}")

            target_timestamp = ds_ww3.TIME.values[target_index]
            target_timestamp = pd.to_datetime(target_timestamp)

            ww3_slice = (
                ds_ww3
                .sel(lat=slice(5, 25), lon=slice(65, 95))
                .sel(TIME=target_timestamp, method="nearest")
                .coarsen(lat=2, lon=2, boundary="trim")
                .mean()
            )

            curr_slice = (
                ds_curr
                .sel(LAT=slice(5, 25), LON=slice(65, 95), DEPTH1_1=0.0)
                .sel(TAXIS=target_timestamp, method="nearest")
                .coarsen(LAT=2, LON=2, boundary="trim")
                .mean()
            )

            wind_vectors = []
            lon_grid, lat_grid = np.meshgrid(ww3_slice.lon.values, ww3_slice.lat.values)
            for lat_val, lon_val, u, v in zip(
                lat_grid.ravel(), lon_grid.ravel(),
                ww3_slice.UWND.values.ravel(), ww3_slice.VWND.values.ravel()
            ):
                if np.isnan(u) or np.isnan(v):
                    continue
                speed = math.sqrt(u ** 2 + v ** 2) * 3.6
                direction = (math.degrees(math.atan2(u, v)) + 180) % 360
                wind_vectors.append({
                    "lat": round(float(lat_val), 2),
                    "lon": round(float(lon_val), 2),
                    "u": round(float(u), 2),
                    "v": round(float(v), 2),
                    "speed_kmh": round(speed, 1),
                    "direction_deg": round(direction, 1),
                })

            current_vectors = []
            lon_grid_c, lat_grid_c = np.meshgrid(curr_slice.LON.values, curr_slice.LAT.values)
            for lat_val, lon_val, u, v in zip(
                lat_grid_c.ravel(), lon_grid_c.ravel(),
                curr_slice.U.values.ravel(), curr_slice.V.values.ravel()
            ):
                if np.isnan(u) or np.isnan(v):
                    continue
                speed = math.sqrt(u ** 2 + v ** 2)
                direction = math.degrees(math.atan2(u, v)) % 360
                current_vectors.append({
                    "lat": round(float(lat_val), 2),
                    "lon": round(float(lon_val), 2),
                    "u": round(float(u), 3),
                    "v": round(float(v), 3),
                    "speed_ms": round(speed, 2),
                    "direction_deg": round(direction, 1),
                })

            grid_data = {
                "wind": wind_vectors,
                "current": current_vectors,
                "timestamp": target_timestamp.isoformat(),
                "day": day,
                "hour": hour,
                "source": "INCOIS WW3 + Currents",
            }

            os.makedirs(os.path.dirname(grid_cache), exist_ok=True)
            with open(grid_cache, "w", encoding="utf-8") as f:
                json.dump(grid_data, f)
            return grid_data
        except Exception:
            import logging
            logging.exception("Failed to generate vector grid")
            raise
