from app.api.services.orca_bsi_engine import VesselProfile
from datetime import datetime
from unittest.mock import patch
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.trip_decision import TripDecisionEngine
from app.api.services.forecast_data import ForecastDataService
from app.core.domain import EnvironmentSnapshot
from app.core.exceptions import DataUnavailableError

def mock_get_grid_nodes():
    return [(15.0, 75.0), (15.1, 75.1), (15.2, 75.2)]
    
def mock_get_environment(lat, lon, timestamp):
    if (lat, lon) not in mock_get_grid_nodes():
        raise DataUnavailableError("Grid missing for these coordinates (Land/OOB)")
    return EnvironmentSnapshot(
        timestamp=timestamp, lat=lat, lon=lon,
        wave_height_m=1.0, wave_steepness=0.015, directional_spread=0.25,
        wind_speed_kmh=10.0, wind_direction_deg=180.0,
        current_speed_ms=0.5, current_direction_deg=180.0, bsi=0
    )

def test_routing_start_on_land():
    with patch('app.api.services.pfz_routing.evaluate_geofence_offline', return_value={"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}), \
         patch.object(ForecastDataService, 'get_environment', side_effect=mock_get_environment), \
         patch.object(ForecastDataService, 'get_grid_nodes', return_value=mock_get_grid_nodes()):
        try:
            # Start point 0.0, 0.0 is not in mock grid nodes
            PFZRoutingService.calculate_optimal_route(
                start_lat=0.0, start_lon=0.0, end_lat=15.2, end_lon=75.2,
                beam_m=4.0, cruising_speed_kn=10.0, departure_time="2026-08-26T12:00:00Z"
            )
            assert False, "Should raise DataUnavailableError when starting on land"
        except DataUnavailableError:
            print("✓ test_routing_start_on_land passed (Properly failed closed)")

def test_routing_zero_distance():
    with patch('app.api.services.pfz_routing.evaluate_geofence_offline', return_value={"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}), \
         patch.object(ForecastDataService, 'get_environment', side_effect=mock_get_environment), \
         patch.object(ForecastDataService, 'get_grid_nodes', return_value=mock_get_grid_nodes()):
        # Start and end are exactly the same
        res = PFZRoutingService.calculate_optimal_route(
            start_lat=15.0, start_lon=75.0, end_lat=15.0, end_lon=75.0,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time="2026-08-26T12:00:00Z"
        )
        # assert res is not None and "route" in res
        assert len(res["path"]) >= 1 # Start and end (or just one if identical)
        assert len(res["snapshots"]) >= 1
        print("✓ test_routing_zero_distance passed")

def test_invalid_departure_time_format():
    with patch('app.api.services.pfz_routing.evaluate_geofence_offline', return_value={"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}), \
         patch.object(ForecastDataService, 'get_environment', side_effect=mock_get_environment), \
         patch.object(ForecastDataService, 'get_grid_nodes', return_value=mock_get_grid_nodes()):
        try:
            PFZRoutingService.calculate_optimal_route(
                start_lat=15.0, start_lon=75.0, end_lat=15.2, end_lon=75.2,
                beam_m=4.0, cruising_speed_kn=10.0, departure_time="INVALID_TIME"
            )
            assert False, "Should raise DataUnavailableError for bad timestamp"
        except DataUnavailableError as e:
            assert "Invalid departure time" in str(e)
            print("✓ test_invalid_departure_time_format passed")
