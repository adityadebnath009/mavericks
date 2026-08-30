from datetime import datetime
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.trip_decision import TripDecisionEngine
from app.api.services.forecast_data import ForecastDataService
from app.core.domain import EnvironmentSnapshot
from app.core.exceptions import DataUnavailableError

def setup_mock_environment(routing):
    def mock_evaluate_geofence(lat, lon):
        return {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}
    routing.evaluate_geofence_offline = mock_evaluate_geofence
    
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
        
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment

def test_routing_start_on_land():
    import app.api.services.pfz_routing as routing
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    
    setup_mock_environment(routing)
    
    try:
        # Start point 0.0, 0.0 is not in mock grid nodes
        PFZRoutingService.calculate_optimal_route(
            start_lat=0.0, start_lon=0.0, end_lat=15.2, end_lon=75.2,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time="2026-08-26T12:00:00Z"
        )
        assert False, "Should raise DataUnavailableError when starting on land"
    except DataUnavailableError:
        print("✓ test_routing_start_on_land passed (Properly failed closed)")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

def test_routing_zero_distance():
    import app.api.services.pfz_routing as routing
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    
    setup_mock_environment(routing)
    
    try:
        # Start and end are exactly the same
        res = PFZRoutingService.calculate_optimal_route(
            start_lat=15.0, start_lon=75.0, end_lat=15.0, end_lon=75.0,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time="2026-08-26T12:00:00Z"
        )
        assert res["decision"] == "RECOMMENDED"
        assert len(res["route_coords"]) >= 1 # Start and end (or just one if identical)
        assert len(res["snapshots"]) >= 1
        print("✓ test_routing_zero_distance passed")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

def test_invalid_departure_time_format():
    import app.api.services.pfz_routing as routing
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    
    setup_mock_environment(routing)
    
    try:
        PFZRoutingService.calculate_optimal_route(
            start_lat=15.0, start_lon=75.0, end_lat=15.2, end_lon=75.2,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time="INVALID_TIME"
        )
        assert False, "Should raise DataUnavailableError for bad timestamp"
    except DataUnavailableError as e:
        assert "Invalid departure_time" in str(e)
        print("✓ test_invalid_departure_time_format passed")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

if __name__ == "__main__":
    print("Running Edge Cases Tests...")
    test_routing_start_on_land()
    test_routing_zero_distance()
    test_invalid_departure_time_format()
    print("All Edge Case Tests Passed!")
