from app.api.services.orca_bsi_engine import VesselProfile
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.forecast_data import ForecastDataService
from app.core.domain import EnvironmentSnapshot

def test_determinism():
    start_lat, start_lon = 15.0, 75.0
    end_lat, end_lon = 15.2, 75.2
    dep_time = "2026-08-26T12:00:00Z"
    
    import app.api.services.pfz_routing as routing
    def mock_evaluate_geofence(lat, lon):
        return {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}
    routing.evaluate_geofence_offline = mock_evaluate_geofence
    
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    
    def mock_get_grid_nodes():
        return [(start_lat, start_lon), (15.1, 75.1), (end_lat, end_lon)]
        
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
        res1 = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time=dep_time
        )
        
        res2 = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time=dep_time
        )
        
        assert res1 == res2
        print("✓ test_determinism passed")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

def test_beam_scaling():
    start_lat, start_lon = 15.0, 75.0
    end_lat, end_lon = 15.2, 75.2
    dep_time = "2026-08-26T12:00:00Z"
    
    import app.api.services.pfz_routing as routing
    def mock_evaluate_geofence(lat, lon):
        return {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}
    routing.evaluate_geofence_offline = mock_evaluate_geofence
    
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    
    def mock_get_grid_nodes():
        return [(start_lat, start_lon), (end_lat, end_lon)]
        
    def mock_get_environment(lat, lon, timestamp):
        return EnvironmentSnapshot(
            timestamp=timestamp, lat=lat, lon=lon,
            wave_height_m=2.5, # High waves
            wave_steepness=0.015, directional_spread=0.25,
            wind_speed_kmh=10.0, wind_direction_deg=180.0,
            current_speed_ms=0.5, current_direction_deg=180.0, bsi=1
        )
        
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment
    
    try:
        # Beam 4.0m -> critical_height = 1.5 * 4 = 6.0m
        # Wave is 2.5, so route is recommended
        res_wide = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time=dep_time
        )
        assert res_wide["decision"] == "RECOMMENDED"
        
        # Beam 1.0m -> critical_height = 1.5 * 1 = 1.5m
        # Wave is 2.5, so route should be completely rejected
        res_narrow = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=1.0, cruising_speed_kn=10.0, departure_time=dep_time
        )
        assert res_narrow["decision"] == "REJECTED_NO_SAFE_ROUTE"
        
        print("✓ test_beam_scaling passed")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

if __name__ == "__main__":
    test_determinism()
    test_beam_scaling()
    print("ALL PHYSICS & DETERMINISM TESTS PASSED")
