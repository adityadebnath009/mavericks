import math
from datetime import datetime, timedelta
from app.api.services.pfz_routing import PFZRoutingService
from app.core.exceptions import DataUnavailableError
from app.api.services.forecast_data import ForecastDataService
from app.core.domain import EnvironmentSnapshot

def test_vessel_speed_impact():
    # We will mock the environment and geofence
    # We want to route from A(15.0, 75.0) to B(15.2, 75.2)
    # The grid will just have A and B.
    
    start_lat, start_lon = 15.0, 75.0
    end_lat, end_lon = 15.2, 75.2
    dep_time = "2026-08-26T12:00:00Z"
    
    # Mock geofence cache globally
    import app.api.services.pfz_routing as routing
    
    def mock_evaluate_geofence(lat, lon):
        return {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}
        
    routing.evaluate_geofence_offline = mock_evaluate_geofence
    
    # Mock ForecastDataService
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    
    def mock_get_grid_nodes():
        return [(start_lat, start_lon), (end_lat, end_lon)]
        
    def mock_get_environment(lat, lon, timestamp):
        return EnvironmentSnapshot(
            timestamp=timestamp, lat=lat, lon=lon,
            wave_height_m=1.0, wave_steepness=0.015, directional_spread=0.25,
            wind_speed_kmh=10.0, wind_direction_deg=180.0,
            current_speed_ms=0.5, current_direction_deg=180.0, bsi=1
        )
        
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment
    
    try:
        # Route at 8 knots
        res_8kn = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=4.0, cruising_speed_kn=8.0, departure_time=dep_time
        )
        
        # Route at 15 knots
        res_15kn = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=4.0, cruising_speed_kn=15.0, departure_time=dep_time
        )
        
        assert res_8kn["decision"] == "RECOMMENDED"
        assert res_15kn["decision"] == "RECOMMENDED"
        
        # Calculate time taken for both
        t_8kn_start = datetime.fromisoformat(res_8kn["snapshots"][0]["time"])
        t_8kn_end = datetime.fromisoformat(res_8kn["snapshots"][-1]["time"])
        dur_8kn = (t_8kn_end - t_8kn_start).total_seconds()
        
        t_15kn_start = datetime.fromisoformat(res_15kn["snapshots"][0]["time"])
        t_15kn_end = datetime.fromisoformat(res_15kn["snapshots"][-1]["time"])
        dur_15kn = (t_15kn_end - t_15kn_start).total_seconds()
        
        # 8 knots should take longer than 15 knots
        assert dur_8kn > dur_15kn
        
        print("✓ test_vessel_speed_impact passed")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

if __name__ == "__main__":
    test_vessel_speed_impact()
    print("ALL ROUTING TESTS PASSED")
