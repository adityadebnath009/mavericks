import re

with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

def_clean = """
    def clean_nan(val, rnd=2):
        import math
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return None
            return round(f, rnd)
        except:
            return None
"""

# Insert clean_nan before _compute_grid if not there
if "def clean_nan" not in content:
    content = content.replace("    def _compute_grid():", def_clean + "\n    def _compute_grid():")

old_props = """                    "properties": {
                        "bsi": val,
                        "hs": round(hs_val, 2),
                        "wind_speed_kmh": round(wind_val, 1),
                        "current_speed_ms": round(curr_val, 2),
                        "wind_dir_deg": round(wind_dir_val, 1),
                        "current_dir_deg": round(curr_dir_val, 1),
                        "center_lat": round(float(lat_c), 4),
                        "center_lon": round(float(lon_c), 4),
                        "color": color
                    }"""

new_props = """                    "properties": {
                        "bsi": val,
                        "hs": clean_nan(hs_val, 2),
                        "wind_speed_kmh": clean_nan(wind_val, 1),
                        "current_speed_ms": clean_nan(curr_val, 2),
                        "wind_dir_deg": clean_nan(wind_dir_val, 1),
                        "current_dir_deg": clean_nan(curr_dir_val, 1),
                        "center_lat": clean_nan(lat_c, 4),
                        "center_lon": clean_nan(lon_c, 4),
                        "color": color
                    }"""

content = content.replace(old_props, new_props)

with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)

import os, glob
for f in glob.glob("cache/safety_grid_*.json"):
    os.remove(f)

