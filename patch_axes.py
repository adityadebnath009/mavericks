import re
with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

content = content.replace("IOYAXIS=", "lat=")
content = content.replace("IOXAXIS=", "lon=")
content = content.replace("grid_slice.IOYAXIS.values", "grid_slice.lat.values")
content = content.replace("grid_slice.IOXAXIS.values", "grid_slice.lon.values")

with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)

import os, glob
for f in glob.glob("cache/safety_grid_*.json"):
    os.remove(f)

