import re

with open("backend/app/api/services/pfz_routing.py", "r") as f:
    content = f.read()

content = content.replace("from app.api.services.forecast_data import ForecastDataService", 
                          "from app.api.services.forecast_data import ForecastDataService\nfrom app.api.services.marine_forecast import MarineForecastService")
content = content.replace("ForecastDataService.get_environment", "MarineForecastService.get_environment")

# Fix env.bsi to handle None (for production where it's stripped out)
content = re.sub(r'env\.bsi', '(env.bsi or 0)', content)

with open("backend/app/api/services/pfz_routing.py", "w") as f:
    f.write(content)
