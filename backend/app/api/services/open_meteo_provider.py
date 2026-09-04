import datetime
from typing import Dict, Any, Tuple, Optional

class OpenMeteoProvider:
    """
    Translates Open-Meteo's raw JSON responses into the domain schema.
    """
    
    @staticmethod
    def _find_nearest_time_idx(times: list, target: datetime.datetime) -> int:
        """Find the index of the closest time in the hourly array."""
        target_ts = target.timestamp()
        min_diff = float('inf')
        best_idx = 0
        for i, t_str in enumerate(times):
            # Open-Meteo returns '2026-09-03T12:00'
            dt = datetime.datetime.fromisoformat(t_str).replace(tzinfo=datetime.timezone.utc)
            diff = abs(dt.timestamp() - target_ts)
            if diff < min_diff:
                min_diff = diff
                best_idx = i
        return best_idx

    @classmethod
    def extract_forecast(cls, marine_data: Dict[str, Any], weather_data: Dict[str, Any], target_time: datetime.datetime) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extracts current environmental state and 24h timeline from the 72h OM response.
        Returns (current_dict, timeline_dict)
        """
        m_hourly = marine_data.get("hourly", {})
        w_hourly = weather_data.get("hourly", {})
        
        times = m_hourly.get("time", [])
        if not times:
            return {}, {}
            
        idx = cls._find_nearest_time_idx(times, target_time)
        
        def safe_get(hourly: dict, key: str, index: int) -> Optional[float]:
            arr = hourly.get(key, [])
            if index < len(arr):
                val = arr[index]
                if val is not None:
                    return float(val)
            return None

        current = {
            "timestamp": target_time,
            "wave_height_m": safe_get(m_hourly, "wave_height", idx),
            "wave_period_s": safe_get(m_hourly, "wave_period", idx),
            "wave_direction_deg": safe_get(m_hourly, "wave_direction", idx),
            "wind_wave_height_m": safe_get(m_hourly, "wind_wave_height", idx),
            "wind_wave_period_s": safe_get(m_hourly, "wind_wave_period", idx),
            "wind_speed_ms": safe_get(w_hourly, "wind_speed_10m", idx) * (1000/3600) if safe_get(w_hourly, "wind_speed_10m", idx) is not None else None, # OM is km/h
            "wind_direction_deg": safe_get(w_hourly, "wind_direction_10m", idx),
            "current_speed_ms": safe_get(m_hourly, "ocean_current_velocity", idx) * (1000/3600) if safe_get(m_hourly, "ocean_current_velocity", idx) is not None else None, # OM is km/h
            "current_direction_deg": safe_get(m_hourly, "ocean_current_direction", idx),
            "sst_c": safe_get(m_hourly, "sea_surface_temperature", idx),
            "directional_spread": None
        }

        # 24h timeline
        timeline = {
            "timestamps": [],
            "wave_height_m": [],
            "wave_period_s": [],
            "wind_speed_ms": [],
            "current_speed_ms": []
        }
        
        end_idx = min(idx + 24, len(times))
        for i in range(idx, end_idx):
            dt = datetime.datetime.fromisoformat(times[i]).replace(tzinfo=datetime.timezone.utc)
            timeline["timestamps"].append(dt)
            timeline["wave_height_m"].append(safe_get(m_hourly, "wave_height", i))
            timeline["wave_period_s"].append(safe_get(m_hourly, "wave_period", i))
            
            ws = safe_get(w_hourly, "wind_speed_10m", i)
            timeline["wind_speed_ms"].append(ws * (1000/3600) if ws is not None else None)
            
            cs = safe_get(m_hourly, "ocean_current_velocity", i)
            timeline["current_speed_ms"].append(cs * (1000/3600) if cs is not None else None)

        return current, timeline
