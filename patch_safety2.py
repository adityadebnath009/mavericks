import re

with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

# Replace the remaining IncoisDatasetResolver.resolve_latest_forecast with pass
content = re.sub(r'ww3_res, _ = IncoisDatasetResolver\.resolve_latest_forecast\(lat, lon, d, purpose="visualization"\)', 'raise Exception("PyDAP removed")', content)

with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)
