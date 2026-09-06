import json
from app.api.services.pfz_routing import PFZRoutingService, haversine_distance
from app.api.services.orca_bsi_engine import VesselProfile, OrcaBsiEngine
from app.api.services.route_bsi_profiler import RouteBsiProfiler
from app.api.services.forecast_data import ForecastDataService
from datetime import datetime

vessel = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
engine = OrcaBsiEngine()
dep_dt = datetime.fromisoformat("2026-09-05T19:11:00+00:00")

route_coords = [
    {"lat": 20.5981, "lon": 88.3671},
    {"lat": 20.2, "lon": 88.0},
    {"lat": 19.8, "lon": 87.6}
]

profiler = RouteBsiProfiler(ForecastDataService, engine)
base = profiler.generate_route_profile(route_coords, vessel, dep_dt)

print(json.dumps(base["route_bsi"]))
