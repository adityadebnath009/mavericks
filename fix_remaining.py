import os
import glob

# 1. Update trip schemas
f = "backend/app/schemas/routing.py"
with open(f, 'r') as fh:
    c = fh.read()
c = c.replace('route_coords: List[List[float]]', 'path: list = []')
with open(f, 'w') as fh:
    fh.write(c)

f = "backend/app/api/services/trip_decision.py"
with open(f, 'r') as fh:
    c = fh.read()
c = c.replace('if route_res.get("decision") == "REJECTED_NO_SAFE_ROUTE":', 'if route_res is None:')
c = c.replace('"route_coords": route_res["route_coords"],', '"path": route_res.get("path", []),')
c = c.replace('"route_coords": route_res.get("route_coords", route_res.get("path", [])),', '"path": route_res.get("path", []),')
c = c.replace('route_res.get("route_coords")', 'route_res.get("path")')
with open(f, 'w') as fh:
    fh.write(c)
    
# test_certification_100.py specific fixes for FastAPI test client
f = "backend/tests/test_certification_100.py"
with open(f, 'r') as fh:
    c = fh.read()
c = c.replace('res["recommended_pfz"]["route_coords"]', 'res["recommended_pfz"]["path"]')
with open(f, 'w') as fh:
    fh.write(c)

