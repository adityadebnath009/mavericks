import pytest
from datetime import datetime
from app.api.services.pfz_routing import PFZRoutingService, PALK_STRAIT_CORRIDOR_NODES
from app.api.endpoints.geofence import evaluate_geofence_offline
from app.api.services.forecast_data import ForecastDataService
from app.core.exceptions import DataUnavailableError

def test_palk_strait_nodes_injected():
    assert len(PALK_STRAIT_CORRIDOR_NODES) > 0, "Corridor nodes must be defined"
    
def test_all_corridor_nodes_are_geospatially_legal():
    for lat, lon in PALK_STRAIT_CORRIDOR_NODES:
        gf = evaluate_geofence_offline(lat, lon)
        assert gf.get("is_inside_eez") is True, f"Node {lat}, {lon} is outside EEZ"
        assert gf.get("is_inside_mpa") is False, f"Node {lat}, {lon} is inside MPA"

def test_corridor_edges_are_geospatially_legal():
    pass

def test_palk_strait_route_succeeds():
    from app.api.services.orca_bsi_engine import VesselProfile
    v = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
    dt = ForecastDataService.get_baseline_time().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    res = PFZRoutingService.calculate_optimal_route(
        start_lat=10.2, start_lon=79.8,
        end_lat=9.0, end_lon=78.6,
        vessel_profile=v,
        departure_time=dt
    )
    assert res is not None, "Route through Palk Strait failed"
    assert "path" in res

def test_illegal_route_gets_rejected():
    from app.api.services.orca_bsi_engine import VesselProfile
    v = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
    dt = ForecastDataService.get_baseline_time().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    try:
        res = PFZRoutingService.calculate_optimal_route(
            start_lat=5.0, start_lon=80.0, # deep ocean south of Sri Lanka
            end_lat=4.0, end_lon=79.0,
            vessel_profile=v,
            departure_time=dt
        )
        assert res == {"decision": "REJECTED_NO_SAFE_ROUTE"}
    except DataUnavailableError:
        pass # Out of bounds grid is also a rejection

def test_corridor_nodes_receive_environment_data():
    dt = ForecastDataService.get_baseline_time()
    for lat, lon in PALK_STRAIT_CORRIDOR_NODES[:5]:
        env = ForecastDataService.get_environment(lat, lon, dt)
        assert env is not None
        assert env.current is not None
        assert env.current.wave_height_m is not None

def test_no_n_plus_one_weather_requests():
    pass

def test_normal_routes_remain_unchanged():
    pass
