from datetime import datetime, timedelta
from unittest.mock import patch
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.forecast_data import ForecastDataService
from app.core.domain import EnvironmentSnapshot

def test_speed_caps_and_floors():
    def mock_evaluate_geofence(lat, lon):
        return {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}
    
    def mock_get_grid_nodes():
        return [(15.0+i*0.1, 75.0+j*0.1) for i in range(3) for j in range(3)]
        
    def mock_get_environment(lat, lon, timestamp):
        return EnvironmentSnapshot(
            timestamp=timestamp, lat=lat, lon=lon,
            wave_height_m=1.0, wave_steepness=0.015, directional_spread=0.25,
            wind_speed_kmh=10.0, wind_direction_deg=180.0,
            current_speed_ms=5.0, current_direction_deg=180.0, bsi=0
        )
        
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment

    with patch("app.api.services.pfz_routing.evaluate_geofence_offline", mock_evaluate_geofence):
        try:
            # Slow floor
            res_slow = PFZRoutingService.calculate_optimal_route(
                start_lat=15.0, start_lon=75.0, end_lat=15.2, end_lon=75.0,
                beam_m=4.0, cruising_speed_kn=1.0, departure_time="2026-08-26T12:00:00Z"
            )
            assert res_slow["decision"] == "RECOMMENDED"
            time_taken = (datetime.fromisoformat(res_slow["snapshots"][-1]["time"]) - datetime.fromisoformat(res_slow["snapshots"][0]["time"])).total_seconds() / 3600.0
            assert time_taken >= 10.0
            
            # Fast cap
            def mock_get_environment_fast(lat, lon, timestamp):
                return EnvironmentSnapshot(
                    timestamp=timestamp, lat=lat, lon=lon,
                    wave_height_m=1.0, wave_steepness=0.015, directional_spread=0.25,
                    wind_speed_kmh=10.0, wind_direction_deg=180.0,
                    current_speed_ms=0.0, current_direction_deg=0.0, bsi=0
                )
            ForecastDataService.get_environment = mock_get_environment_fast
            
            res_fast = PFZRoutingService.calculate_optimal_route(
                start_lat=15.0, start_lon=75.0, end_lat=15.2, end_lon=75.0,
                beam_m=4.0, cruising_speed_kn=100.0, departure_time="2026-08-26T12:00:00Z"
            )
            time_taken_fast = (datetime.fromisoformat(res_fast["snapshots"][-1]["time"]) - datetime.fromisoformat(res_fast["snapshots"][0]["time"])).total_seconds() / 3600.0
            assert time_taken_fast >= 0.7
            
            print("✓ test_speed_caps_and_floors passed")
        finally:
            ForecastDataService.get_environment = original_get_env
            ForecastDataService.get_grid_nodes = original_get_nodes

def test_impenetrable_geofence_wall():
    def mock_evaluate_geofence(lat, lon):
        is_mpa = True if lon >= 75.2 else False
        return {"is_inside_eez": True, "is_inside_mpa": is_mpa, "distance_to_border_km": 50.0}
    
    def mock_get_grid_nodes():
        return [(15.0+i*0.1, 75.0+j*0.1) for i in range(3) for j in range(3)]
        
    def mock_get_environment(lat, lon, timestamp):
        return EnvironmentSnapshot(
            timestamp=timestamp, lat=lat, lon=lon,
            wave_height_m=1.0, wave_steepness=0.015, directional_spread=0.25,
            wind_speed_kmh=10.0, wind_direction_deg=180.0,
            current_speed_ms=0.0, current_direction_deg=180.0, bsi=0
        )
        
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment

    with patch("app.api.services.pfz_routing.evaluate_geofence_offline", mock_evaluate_geofence):
        try:
            res = PFZRoutingService.calculate_optimal_route(
                start_lat=15.0, start_lon=75.0, end_lat=15.0, end_lon=75.2,
                beam_m=4.0, cruising_speed_kn=10.0, departure_time="2026-08-26T12:00:00Z"
            )
            assert res["decision"] == "REJECTED_NO_SAFE_ROUTE"
            print("✓ test_impenetrable_geofence_wall passed")
        finally:
            ForecastDataService.get_environment = original_get_env
            ForecastDataService.get_grid_nodes = original_get_nodes

def test_extreme_bsi_rejection():
    def mock_evaluate_geofence(lat, lon):
        return {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 50.0}
    
    def mock_get_grid_nodes():
        return [(15.0+i*0.1, 75.0+j*0.1) for i in range(3) for j in range(3)]
        
    def mock_get_environment(lat, lon, timestamp):
        return EnvironmentSnapshot(
            timestamp=timestamp, lat=lat, lon=lon,
            wave_height_m=1.0, wave_steepness=0.015, directional_spread=0.25,
            wind_speed_kmh=10.0, wind_direction_deg=180.0,
            current_speed_ms=0.0, current_direction_deg=180.0, bsi=5
        )
        
    original_get_env = ForecastDataService.get_environment
    original_get_nodes = ForecastDataService.get_grid_nodes
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment

    with patch("app.api.services.pfz_routing.evaluate_geofence_offline", mock_evaluate_geofence):
        try:
            res = PFZRoutingService.calculate_optimal_route(
                start_lat=15.0, start_lon=75.0, end_lat=15.2, end_lon=75.2,
                beam_m=4.0, cruising_speed_kn=10.0, departure_time="2026-08-26T12:00:00Z"
            )
            assert res["decision"] == "REJECTED_NO_SAFE_ROUTE"
            print("✓ test_extreme_bsi_rejection passed")
        finally:
            ForecastDataService.get_environment = original_get_env
            ForecastDataService.get_grid_nodes = original_get_nodes

if __name__ == "__main__":
    print("Running Extreme Edge Cases Tests...")
    test_speed_caps_and_floors()
    test_impenetrable_geofence_wall()
    test_extreme_bsi_rejection()
    print("All Extreme Edge Case Tests Passed!")
