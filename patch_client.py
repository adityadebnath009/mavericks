import re

with open("backend/app/api/services/open_meteo_client.py", "r") as f:
    content = f.read()

old_hourly = '"hourly": "wave_height,wave_period,wave_direction,wind_wave_height,wind_wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",'
new_hourly = '"hourly": "wave_height,wave_period,wave_direction,wind_wave_height,wind_wave_period,wind_wave_direction,swell_wave_height,swell_wave_direction,swell_wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",'

content = content.replace(old_hourly, new_hourly)

with open("backend/app/api/services/open_meteo_client.py", "w") as f:
    f.write(content)
