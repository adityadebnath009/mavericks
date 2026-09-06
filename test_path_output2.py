import json
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.orca_bsi_engine import VesselProfile

vessel = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
res = PFZRoutingService.calculate_optimal_route(
    start_lat=20.5981,
    start_lon=88.3671,
    end_lat=16.0748,
    end_lon=84.2596,
    vessel_profile=vessel,
    departure_time="2026-09-05T19:11:00Z"
)
print("Path entry 0:", json.dumps(res["path"][0]))
print("Path entry 8 (the red one):", json.dumps(res["path"][8]))
