import os

f = "backend/tests/test_certification_100.py"
with open(f, 'r') as fh: c = fh.read()

# We want to change:
# assert full_path_coords == res["path"]
# to:
# assert full_path_coords == [[p["lat"], p["lon"]] for p in res["path"]]

c = c.replace('assert full_path_coords == res["path"]', 'assert full_path_coords == [[p["lat"], p["lon"]] for p in res["path"]]')

with open(f, 'w') as fh: fh.write(c)
