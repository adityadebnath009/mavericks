import os

f = "backend/tests/test_extreme_edge_cases.py"
with open(f, 'r') as fh: c = fh.read()
# Find test_extreme_bsi_rejection
import re
c = re.sub(r'wave_height_m=1\.0', 'wave_height_m=20.0', c)
c = re.sub(r'wind_speed_kmh=10\.0', 'wind_speed_kmh=150.0', c)
with open(f, 'w') as fh: fh.write(c)

