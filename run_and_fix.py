import subprocess
import os

# Let's just fix the known culprits properly.
# Trip decisions returned by trip.py:
f = "backend/app/api/endpoints/trip.py"
# the Pydantic schema TripAnalysisResponse uses decision: TripDecision, recommended_pfz: RecommendedTrip

# Wait, the easiest way to fix the certification tests without rewriting 100 asserts is 
# to just revert my regex hack on test_certification_100.py and cleanly use sed to ONLY change route_coords to path.
os.system("git checkout backend/tests/test_certification_100.py backend/tests/test_risk_segments.py backend/tests/test_extreme_edge_cases.py backend/tests/test_route_bsi_profiler.py backend/app/schemas/routing.py backend/app/api/services/trip_decision.py")

# Now let's carefully apply the MINIMAL required changes:

# 1. Trip schema: route_coords -> path
with open("backend/app/schemas/routing.py", "r") as f: c = f.read()
c = c.replace("route_coords: List[List[float]]", "path: List[dict] = []")
with open("backend/app/schemas/routing.py", "w") as f: f.write(c)

# 2. trip_decision: adapt to new routing response
with open("backend/app/api/services/trip_decision.py", "r") as f: c = f.read()
c = c.replace('route_res.get("decision") == "REJECTED_NO_SAFE_ROUTE"', 'route_res is None')
c = c.replace('"route_coords": route_res["route_coords"],', '"path": route_res.get("path", []),')
c = c.replace('route_res.get("route_coords", [])', 'route_res.get("path", [])')
with open("backend/app/api/services/trip_decision.py", "w") as f: f.write(c)

# 3. Certification tests:
with open("backend/tests/test_certification_100.py", "r") as f: c = f.read()
# The routing response changed completely. 
# For test_group_g_routing_*, the response is the new PFZRoutingService schema (route, optimization, path)
c = c.replace('res["decision"] == "RECOMMENDED"', 'res is not None and "route" in res')
c = c.replace('res["decision"] == "REJECTED_NO_SAFE_ROUTE"', 'res is None')
c = c.replace('res["route_coords"]', 'res["path"]')
c = c.replace('res["recommended_pfz"]["route_coords"]', 'res["recommended_pfz"]["path"]')
with open("backend/tests/test_certification_100.py", "w") as f: f.write(c)

