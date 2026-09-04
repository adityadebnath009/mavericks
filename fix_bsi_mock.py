f = "backend/tests/test_route_bsi_profiler.py"
with open(f, "r") as fh: c = fh.read()
c = c.replace("def get_environment(self, lat, lon):", "def get_environment(self, lat, lon, timestamp=None):")
with open(f, "w") as fh: fh.write(c)
