import re

f = "backend/app/api/services/trip_decision.py"
with open(f, 'r') as fh:
    c = fh.read()

c = c.replace('route_res.get("decision") == "REJECTED_NO_SAFE_ROUTE"', 'route_res is None')
c = c.replace('route_res["route_coords"]', 'route_res.get("route_coords", route_res.get("path", []))')
# Wait, actually, let's just make it return path since calculate_optimal_route returns path now.
# But wait, RecommendedTrip schema STILL expects route_coords. I should rename it in the schema if it's supposed to be path.
# In my previous script `fix_pydantic_and_remaining_tests.py`, I replaced route_coords with path in PFZRoute, but maybe NOT in RecommendedTrip?
