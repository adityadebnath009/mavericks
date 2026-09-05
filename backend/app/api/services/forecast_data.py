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
        from datetime import timezone
        # Dynamically centralized baseline.
        return datetime(2026, 8, 26, 0, 0, 0, tzinfo=timezone.utc)

    @classmethod
    def resolve_forecast_time(cls, departure_time: str) -> float:
        baseline_dt = cls.get_baseline_time()
        try:
            dt_str = departure_time.replace("Z", "")
            if "T" in dt_str:
                dep_dt = datetime.fromisoformat(dt_str)
            else:
                dep_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            from datetime import timezone
            if dep_dt.tzinfo is None:
                dep_dt = dep_dt.replace(tzinfo=timezone.utc)
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
        from datetime import timezone
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
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
        try:
            nodes_t0 = cls.load_grid(t0_d, t0_h)
        except (FileNotFoundError, OSError, EOFError) as e:
            raise DataUnavailableError(f"Grid data unavailable for T0 ({t0_d}d {t0_h}h).") from e
        
        props_t0 = cls._find_nearest_props(lat, lon, nodes_t0)
        
        if elapsed_hours == float(t0_hours):
            # Exact boundary (e.g. 72h), no T1 needed
            props_t1 = props_t0
            fraction = 0.0
        else:
            t1_d, t1_h = get_dh(t1_hours)
            try:
                nodes_t1 = cls.load_grid(t1_d, t1_h)
            except (FileNotFoundError, OSError, EOFError) as e:
                raise DataUnavailableError(f"Grid data unavailable for T1 ({t1_d}d {t1_h}h).") from e
            props_t1 = cls._find_nearest_props(lat, lon, nodes_t1)
            fraction = (elapsed_hours - t0_hours) / 3.0
        
        def interp(key, default_val=None):
            v0 = props_t0.get(key)
            v1 = props_t1.get(key)
            if v0 is None or v1 is None:
                if default_val is not None:
                    v0 = v0 if v0 is not None else default_val
                    v1 = v1 if v1 is not None else default_val
                else:
                    raise DataUnavailableError(f"Missing required environmental variable '{key}' at coordinates ({lat}, {lon}) for timestamps T0/T1.")
            return v0 + (v1 - v0) * fraction

        hs = interp("hs")
        stp = interp("stp")
        spr_deg = interp("spr")
        hsea_i = interp("hsea_initial")
        hsea_f = interp("hsea_final")
        
        bsi = 0

        from app.core.domain import EnvironmentalConditions, TimelineSeries, ProvenanceRecord
        return EnvironmentSnapshot(
            current=EnvironmentalConditions(
                timestamp=timestamp,
                wave_height_m=hs,
                wind_speed_ms=interp("wind_speed_kmh") / 3.6 if interp("wind_speed_kmh") else 0.0,
                wind_direction_deg=interp("wind_dir_deg"),
                current_speed_ms=interp("current_speed_ms"),
                current_direction_deg=interp("current_dir_deg"),
                directional_spread=ss
            ),
            timeline=TimelineSeries(),
            provenance={},
            lat=lat,
            lon=lon,
            wave_steepness=stp,
            bsi=bsi
        )
