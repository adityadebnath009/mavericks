import re

with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

# 1. get_safety_assessment:
# Find the try block that does ww3_res, curr_res = IncoisDatasetResolver.resolve_latest_forecast
# and replace it with just incois_success = False
pattern1 = r'try:\s+ww3_res, curr_res = IncoisDatasetResolver\.resolve_latest_forecast\(.*?\s+incois_success = True\s+except Exception as e:\s+# Fallback to local / Open-Meteo in case of land grid or other parse errors\s+pass'
content = re.sub(pattern1, "incois_success = False\n    pass", content, flags=re.DOTALL)

# 2. get_point_forecast_timeline:
pattern2 = r'try:\s+ww3_res, curr_res = IncoisDatasetResolver\.resolve_latest_forecast\(.*?\s+except Exception:\s+pass'
content = re.sub(pattern2, "pass", content, flags=re.DOTALL)

# 3. get_safety_grid:
# ensure we don't try to compute if force_refresh=True
pattern3 = r'ww3_res, curr_res = IncoisDatasetResolver\.resolve_latest_forecast\(.*?_compute_grid\(\)'
# I'll just change `force_refresh` to always False in the endpoint definition
content = content.replace("force_refresh: bool = Query(False, description=\"Force bypass cache\")", "force_refresh: bool = Query(False, description=\"Force bypass cache (disabled)\")")
content = content.replace("if force_refresh or not os.path.exists(cache_path):", "if not os.path.exists(cache_path):")


with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)

