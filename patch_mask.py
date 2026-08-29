import re
with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

old_mask = """                val = int(bsi[i, j])
                hs_val = float(hs[i, j])
                if np.isnan(val) or np.isnan(hs_val) or hs_val <= 0.0:
                    continue  # Skip land cells"""

new_mask = """                val = int(bsi[i, j])
                hs_val = float(hs[i, j])
                wind_val = float(wind_speed_kmh[i, j])
                if np.isnan(val) or np.isnan(hs_val) or hs_val <= 0.0 or np.isnan(wind_val):
                    continue  # Skip land cells"""

content = content.replace(old_mask, new_mask)
with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)
