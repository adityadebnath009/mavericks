import json
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.orca_bsi_engine import VesselProfile

vessel = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
try:
    res = PFZRoutingService.calculate_optimal_route(
        start_lat=20.5981,
        start_lon=88.3671,
        end_lat=16.0748,
        end_lon=84.2596,
        vessel_profile=vessel,
        departure_time="2026-09-10T19:11:00Z" # 4 days in the future
    )
    if res:
        print("Success! Route found.")
    else:
        print("Failed: returned None")
except Exception as e:
    print("Exception:", e)
