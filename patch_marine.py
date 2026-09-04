import re

with open("backend/app/api/services/marine_forecast.py", "r") as f:
    content = f.read()

old_block = """            wind_wave_height_m=current_data.get("wind_wave_height_m"),
            wind_wave_period_s=current_data.get("wind_wave_period_s"),
            wind_speed_ms=current_data.get("wind_speed_ms"),"""

new_block = """            wind_wave_height_m=current_data.get("wind_wave_height_m"),
            wind_wave_period_s=current_data.get("wind_wave_period_s"),
            wind_wave_direction_deg=current_data.get("wind_wave_direction"),
            swell_wave_height_m=current_data.get("swell_wave_height"),
            swell_wave_period_s=current_data.get("swell_wave_period"),
            swell_wave_direction_deg=current_data.get("swell_wave_direction"),
            wind_speed_ms=current_data.get("wind_speed_ms"),"""

content = content.replace(old_block, new_block)

with open("backend/app/api/services/marine_forecast.py", "w") as f:
    f.write(content)
