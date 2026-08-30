from datetime import datetime
from app.api.services.pfz_routing import PFZRoutingService
from app.core.exceptions import DataUnavailableError
from app.api.services.forecast_data import ForecastDataService
from app.core.domain import EnvironmentSnapshot

def test_risk_segments():
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
        # Create a changing environment
        # Node 1: LOW
        # Node 2: HIGH
        # Node 3: HIGH
        
        hs = 0.5
        bsi = 0
        
        if lat >= 15.1:
            hs = 2.5 # HIGH risk
            bsi = 2
            
        return EnvironmentSnapshot(
            timestamp=timestamp, lat=lat, lon=lon,
            wave_height_m=hs, wave_steepness=0.015, directional_spread=0.25,
            wind_speed_kmh=10.0, wind_direction_deg=180.0,
            current_speed_ms=0.5, current_direction_deg=180.0, bsi=bsi
        )
        
    ForecastDataService.get_grid_nodes = mock_get_grid_nodes
    ForecastDataService.get_environment = mock_get_environment
    
    try:
        res = PFZRoutingService.calculate_optimal_route(
            start_lat, start_lon, end_lat, end_lon,
            beam_m=4.0, cruising_speed_kn=10.0, departure_time=dep_time
        )
        
        assert "segments" in res
        segments = res["segments"]
        snapshots = res["snapshots"]
        
        # Verify Snapshots have risk
        assert snapshots[0]["risk"] == "LOW"
        assert snapshots[-1]["risk"] == "HIGH"
        
        # Verify Segments break properly
        assert len(segments) >= 2
        assert segments[0]["risk"] == "LOW"
        assert segments[-1]["risk"] == "HIGH"
        
        # Segment arrays should overlap
        assert segments[0]["coordinates"][-1] == segments[1]["coordinates"][0]
        
        print("✓ test_risk_segments passed")
    finally:
        ForecastDataService.get_environment = original_get_env
        ForecastDataService.get_grid_nodes = original_get_nodes

if __name__ == "__main__":
    test_risk_segments()
    print("ALL RISK SEGMENT TESTS PASSED")
