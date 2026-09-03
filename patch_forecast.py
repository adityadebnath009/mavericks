import re

with open("backend/app/api/services/forecast_data.py", "r") as f:
    content = f.read()

old_return = """        return EnvironmentSnapshot(
            timestamp=timestamp,
            lat=lat,
            lon=lon,
            wave_height_m=hs,
            wave_steepness=stp,
            directional_spread=ss,
            wind_speed_kmh=interp("wind_speed_kmh"),
            wind_direction_deg=interp("wind_dir_deg"),
            current_speed_ms=interp("current_speed_ms"),
            current_direction_deg=interp("current_dir_deg"),
            bsi=bsi
        )"""

new_return = """        from app.core.domain import EnvironmentalConditions, TimelineSeries, ProvenanceRecord
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
        )"""

content = content.replace(old_return, new_return)

with open("backend/app/api/services/forecast_data.py", "w") as f:
    f.write(content)
