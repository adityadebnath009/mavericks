import os
import math
import pickle
import concurrent.futures
import time
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr


class IncoisDatasetResolver:
    """Resolve the latest INCOIS WW3/current datasets and expose exact forecast slices."""

    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
    _url_cache = {}
    _url_cache_time = {}
    _ds_cache = {}
    _ds_cache_time = {}

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
            url_path = dataset.attrib.get("urlPath", "")
            if not name.startswith(prefix) or not name.endswith(".nc") or not url_path:
                continue

            modified = None
            for date_node in dataset.findall("thredds:date", namespace):
                if date_node.attrib.get("type") == "modified" and date_node.text:
                    try:
                        modified = datetime.fromisoformat(date_node.text.strip().replace("Z", "+00:00"))
                    except Exception:
                        pass

            candidates.append({"name": name, "url_path": url_path, "modified": modified})

        if not candidates:
            raise RuntimeError(f"No {prefix} NetCDF datasets found in {catalog_url}")

        candidates.sort(
            key=lambda item: (
                item["modified"] is not None,
                item["modified"] or datetime.min,
                item["name"],
            ),
            reverse=True,
        )
        return "https://www.incois.gov.in/thredds/dodsC/" + candidates[0]["url_path"]

    @classmethod
    def get_ww3_url(cls):
        now = time.time()
        if "ww3" not in cls._url_cache or now - cls._url_cache_time.get("ww3", 0) >= 600:
            cls._url_cache["ww3"] = cls._get_latest_catalog_dataset(
                "https://www.incois.gov.in/thredds/catalog/osf/ww3/catalog.xml",
                "rsmc_nio_ww3_",
            )
            cls._url_cache_time["ww3"] = now
        return cls._url_cache["ww3"]

    @classmethod
    def get_currents_url(cls):
        now = time.time()
        if "currents" not in cls._url_cache or now - cls._url_cache_time.get("currents", 0) >= 600:
            cls._url_cache["currents"] = cls._get_latest_catalog_dataset(
                "https://www.incois.gov.in/thredds/catalog/osf/currents/catalog.xml",
                "CURRENTS_IO_",
            )
            cls._url_cache_time["currents"] = now
        return cls._url_cache["currents"]

    @classmethod
    def get_cache_paths(cls, lat: float, lon: float, day: int):
        ww3_dir = os.path.join(cls.CACHE_DIR, "ww3")
        currents_dir = os.path.join(cls.CACHE_DIR, "currents")
        os.makedirs(ww3_dir, exist_ok=True)
        os.makedirs(currents_dir, exist_ok=True)
        key = f"lat_{round(lat, 3)}_lon_{round(lon, 3)}_day_{day}.pkl"
        return os.path.join(ww3_dir, key), os.path.join(currents_dir, key)

    @classmethod
    def _get_dataset(cls, url: str):
        now = time.time()
        if url in cls._ds_cache and now - cls._ds_cache_time.get(url, 0) < 300:
            return cls._ds_cache[url]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ds = xr.open_dataset(url, engine="pydap")
        cls._ds_cache[url] = ds
        cls._ds_cache_time[url] = now
        return ds

    @classmethod
    def resolve_latest_forecast(cls, lat: float, lon: float, day: int):
        ww3_cache_file, curr_cache_file = cls.get_cache_paths(lat, lon, day)

        if os.path.exists(ww3_cache_file) and os.path.exists(curr_cache_file):
            try:
                with open(ww3_cache_file, "rb") as f:
                    ww3_data = pickle.load(f)
                with open(curr_cache_file, "rb") as f:
                    curr_data = pickle.load(f)
                return ww3_data, curr_data
            except Exception:
                pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(cls._fetch_remote, lat, lon, day, ww3_cache_file, curr_cache_file)
            try:
                return future.result(timeout=4.0)
            except concurrent.futures.TimeoutError:
                raise TimeoutError("INCOIS OPENDAP remote server timed out.")

    @classmethod
    def _fetch_remote(cls, lat: float, lon: float, day: int, ww3_cache_file: str, curr_cache_file: str):
        try:
            ds_ww3 = cls._get_dataset(cls.get_ww3_url())
            ds_curr = cls._get_dataset(cls.get_currents_url())

            ww3_slice = ds_ww3.sel(lat=lat, lon=lon, method="nearest")
            curr_slice = ds_curr.sel(LAT=lat, LON=lon, DEPTH1_1=0.0, method="nearest")

            start_idx = (day - 1) * 8
            target_indices = list(range(max(0, start_idx - 2), min(len(ds_ww3.TIME), start_idx + 8)))
            ww3_subset = ww3_slice.isel(TIME=target_indices)

            times_ww3 = [str(t) for t in ww3_subset.TIME.values]
            hs = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.HS.values]
            stp = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.STP.values]
            spr_raw = [float(v) if not np.isnan(v) else 30.0 for v in ww3_subset.SPR.values]
            spr = [math.sqrt(2.0 * (1.0 - math.cos(math.radians(v)))) for v in spr_raw]
            mwd = [float(v) if not np.isnan(v) else None for v in ww3_subset.MWD.values]
            t02 = [float(v) if not np.isnan(v) else None for v in ww3_subset.T02.values]
            u_wnd = [float(v) if not np.isnan(v) else None for v in ww3_subset.UWND.values]
            v_wnd = [float(v) if not np.isnan(v) else None for v in ww3_subset.VWND.values]
            hsea = [float(v) if not np.isnan(v) else None for v in ww3_subset.PHS00.values]

            offset = 2 if start_idx - 2 >= 0 else 0
            ww3_records = []
            curr_records = []

            for k in range(8):
                idx = offset + k
                lookback_idx = idx - 2 if idx - 2 >= 0 else idx
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

            with open(ww3_cache_file, "wb") as f:
                pickle.dump(ww3_records, f)
            with open(curr_cache_file, "wb") as f:
                pickle.dump(curr_records, f)

            return ww3_records, curr_records
        except Exception as e:
            raise RuntimeError(f"INCOIS Remote fetch error: {e}") from e

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
            ds_ww3 = cls._get_dataset(cls.get_ww3_url())
            ds_curr = cls._get_dataset(cls.get_currents_url())

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
