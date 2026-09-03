import re

with open("backend/app/api/services/pfz_routing.py", "r") as f:
    content = f.read()

# Imports
content = content.replace("from app.api.services.forecast_data import ForecastDataService", 
                          "from app.api.services.forecast_data import ForecastDataService\nfrom app.api.services.marine_forecast import MarineForecastService")

# get_environment calls
content = content.replace("ForecastDataService.get_environment", "MarineForecastService.get_environment")

# Fix env properties in routing A* and formatting
content = re.sub(r'env\.wave_height_m', '(env.current.wave_height_m or 0.0)', content)
content = re.sub(r'env\.bsi', '0', content)
content = re.sub(r'env\.current_direction_deg', '(env.current.current_direction_deg or 0.0)', content)
content = re.sub(r'env\.current_speed_ms', '(env.current.current_speed_ms or 0.0)', content)
content = re.sub(r'env\.wind_speed_kmh', '((env.current.wind_speed_ms or 0.0) * 3.6)', content)
content = re.sub(r'env\.wind_direction_deg', '(env.current.wind_direction_deg or 0.0)', content)

with open("backend/app/api/services/pfz_routing.py", "w") as f:
    f.write(content)
