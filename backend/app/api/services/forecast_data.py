import os
import json
import logging
import math
from datetime import datetime
from typing import Tuple, List

from app.core.exceptions import DataUnavailableError
from app.core.domain import EnvironmentSnapshot

logger = logging.getLogger(__name__)

class ForecastDataService:
    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
    
    _grid_cache = {}
    _spatial_tolerance_km = 15.0  # Roughly 0.15 degrees tolerance for a 0.4 deg grid

    @classmethod
    def get_baseline_time(cls) -> datetime:
        # Dynamically centralized baseline.
        return datetime(2026, 8, 26, 0, 0, 0)

    @classmethod
    def resolve_forecast_time(cls, departure_time: str) -> float:
        baseline_dt = cls.get_baseline_time()
        try:
            dt_str = departure_time.replace("Z", "")
            if "T" in dt_str:
                dep_dt = datetime.fromisoformat(dt_str)
            else:
                dep_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            raise DataUnavailableError(f"Invalid departure_time format: {departure_time}") from e
            
        elapsed_sec = (dep_dt - baseline_dt).total_seconds()
        if elapsed_sec < 0:
            raise DataUnavailableError("Departure time is before the forecast baseline.")
            
        elapsed_hours = elapsed_sec / 3600.0
        if elapsed_hours > 72.0:
            raise DataUnavailableError("Departure time exceeds 72 hour forecast window.")
            
        return elapsed_hours

    @classmethod
    def load_grid(cls, day: int, hour: int) -> List[Tuple[float, float, dict]]:
        if (day, hour) in cls._grid_cache:
            return cls._grid_cache[(day, hour)]
            
        cache_path = os.path.join(cls.CACHE_DIR, f"safety_grid_day_{day}_hour_{hour}.json")
        if not os.path.exists(cache_path):
            raise DataUnavailableError(f"Forecast grid missing for day {day} hour {hour}")
            
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                grid_geojson = json.load(f)
            
            nodes = []
            for feat in grid_geojson.get("features", []):
                props = feat["properties"]
                c_lat = props.get("center_lat")
                c_lon = props.get("center_lon")
                if c_lat is not None and c_lon is not None:
                    nodes.append((c_lat, c_lon, props))
                    
            if not nodes:
                raise DataUnavailableError(f"Grid for day {day} hour {hour} is empty.")
                
            cls._grid_cache[(day, hour)] = nodes
            return nodes
        except Exception as e:
            raise DataUnavailableError(f"Failed to load grid for day {day} hour {hour}: {e}")

    @classmethod
    def get_grid_nodes(cls) -> List[Tuple[float, float]]:
        """Returns the base geometry nodes of the environment for routing algorithms."""
        # Just load day 1 hour 12 as representative of the grid geometry
        nodes = cls.load_grid(1, 12)
        return [(n[0], n[1]) for n in nodes]

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    def _find_nearest_props(cls, lat: float, lon: float, nodes: List[Tuple[float, float, dict]]) -> dict:
        min_dist = float('inf')
        nearest_props = None
        
        for n_lat, n_lon, props in nodes:
            dist = cls._haversine_distance(lat, lon, n_lat, n_lon)
            if dist < min_dist:
                min_dist = dist
                nearest_props = props
                
        if min_dist > cls._spatial_tolerance_km:
            raise DataUnavailableError(f"Coordinates ({lat:.2f}, {lon:.2f}) out of bounds. Nearest grid cell is {min_dist:.1f} km away (tolerance: {cls._spatial_tolerance_km} km).")
            
        return nearest_props

    @classmethod
    def get_environment(cls, lat: float, lon: float, timestamp: datetime) -> EnvironmentSnapshot:
        baseline_dt = cls.get_baseline_time()
        elapsed_sec = (timestamp - baseline_dt).total_seconds()
        
        if elapsed_sec < 0 or elapsed_sec > 72.0 * 3600:
            raise DataUnavailableError(f"Timestamp {timestamp} is outside the 72-hour forecast window.")
            
        elapsed_hours = elapsed_sec / 3600.0
        
        t0_hours = int(elapsed_hours // 3) * 3
        t1_hours = t0_hours + 3
        
        def get_dh(h_elapsed):
            d = int(h_elapsed // 24) + 1
            h = int(h_elapsed % 24)
            return d, h
            
        t0_d, t0_h = get_dh(t0_hours)
        nodes_t0 = cls.load_grid(t0_d, t0_h)
        props_t0 = cls._find_nearest_props(lat, lon, nodes_t0)
        
        if t1_hours > 71:
            props_t1 = props_t0
        else:
            t1_d, t1_h = get_dh(t1_hours)
            try:
                nodes_t1 = cls.load_grid(t1_d, t1_h)
                props_t1 = cls._find_nearest_props(lat, lon, nodes_t1)
            except DataUnavailableError:
                props_t1 = props_t0
                
        # Temporal interpolation
        fraction = (elapsed_hours - t0_hours) / 3.0
        
        def interp(v0, v1):
            if v0 is None or v1 is None:
                return v0 or v1 or 0.0
            return v0 + (v1 - v0) * fraction

        # BSI is categorical discrete, take t0
        bsi = props_t0.get("bsi", 0)

        return EnvironmentSnapshot(
            timestamp=timestamp,
            lat=lat,
            lon=lon,
            wave_height_m=interp(props_t0.get("hs"), props_t1.get("hs")),
            wave_steepness=interp(props_t0.get("stp", 0.015), props_t1.get("stp", 0.015)),
            directional_spread=interp(props_t0.get("spr", 0.25), props_t1.get("spr", 0.25)),
            wind_speed_kmh=interp(props_t0.get("wind_speed_kmh"), props_t1.get("wind_speed_kmh")),
            wind_direction_deg=interp(props_t0.get("wind_dir_deg"), props_t1.get("wind_dir_deg")),
            current_speed_ms=interp(props_t0.get("current_speed_ms"), props_t1.get("current_speed_ms")),
            current_direction_deg=interp(props_t0.get("current_dir_deg"), props_t1.get("current_dir_deg")),
            bsi=bsi
        )
