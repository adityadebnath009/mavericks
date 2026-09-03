import re

with open("backend/app/api/services/pfz_routing.py", "r") as f:
    content = f.read()

# Replace all occurrences of env.wave_height_m with (env.wave_height_m or 0.0) where it's used in math/comparisons
# Actually, just replacing it everywhere is safest:
content = re.sub(r'env\.wave_height_m', '(env.wave_height_m or 0.0)', content)
content = re.sub(r'env\.current_speed_ms', '(env.current_speed_ms or 0.0)', content)
content = re.sub(r'env\.wind_speed_kmh', '(env.wind_speed_kmh or 0.0)', content)
# We already did env.bsi -> (env.bsi or 0), but wait, the previous patch might have missed some or I did it wrong. Let's do it cleanly:
content = content.replace("(env.bsi or 0)", "env.bsi") # revert first
content = re.sub(r'env\.bsi', '(env.bsi or 0)', content)

# But wait, replacing `env.wave_height_m` blindly might cause syntax errors like `(env.wave_height_m or 0.0) >= critical_height` which is valid Python.

with open("backend/app/api/services/pfz_routing.py", "w") as f:
    f.write(content)
