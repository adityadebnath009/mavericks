import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.exceptions import DataUnavailableError

client = TestClient(app)

def test_p0_api_contract():
    """Test 1: API contract POST /api/pfz/route"""
    print("Running Test 1...")
    with patch("app.api.services.pfz_routing.PFZRoutingService.calculate_optimal_route") as mock_route:
        mock_route.return_value = {"decision": "RECOMMENDED"}
        res = client.post("/api/pfz/route", json={
            "start": {"lat": 15.0, "lon": 72.0},
            "end": {"lat": 15.5, "lon": 72.5},
            "beam_m": 2.0,
            "cruising_speed_kn": 8.0,
            "departure_time": "2026-08-27T12:00:00Z"
        })
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json() == {"decision": "RECOMMENDED"}
        
        args, kwargs = mock_route.call_args
        assert kwargs["cruising_speed_kn"] == 8.0
        assert kwargs["departure_time"] == "2026-08-27T12:00:00Z"
    print("Test 1 passed.")

def test_p0_speed_sensitivity():
    """Test 2: Speed sensitivity"""
    print("Running Test 2...")
    from app.api.services.pfz_routing import PFZRoutingService
    route_8kn = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    route_12kn = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=12.0, departure_time="2026-08-27T12:00:00Z"
    )
    
    from datetime import datetime
    t0_8 = datetime.fromisoformat(route_8kn["snapshots"][0]["time"])
    t1_8 = datetime.fromisoformat(route_8kn["snapshots"][-1]["time"])
    t0_12 = datetime.fromisoformat(route_12kn["snapshots"][0]["time"])
    t1_12 = datetime.fromisoformat(route_12kn["snapshots"][-1]["time"])
    
    assert (t1_8 - t0_8).total_seconds() > (t1_12 - t0_12).total_seconds()
    print("Test 2 passed.")

def test_p0_temporal_sensitivity():
    """Test 3: Temporal sensitivity"""
    print("Running Test 3...")
    from app.api.services.pfz_routing import PFZRoutingService
    route_12 = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    route_15 = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T15:00:00Z"
    )
    
    assert route_12["snapshots"][0]["time"] != route_15["snapshots"][0]["time"]
    print("Test 3 passed.")

def test_p0_missing_t1():
    """Test 4: Missing T1 raises DataUnavailableError"""
    print("Running Test 4...")
    from app.api.services.forecast_data import ForecastDataService
    with patch("app.api.services.forecast_data.ForecastDataService.load_grid") as mock_load:
        def side_effect(d, h):
            if h == 15:
                raise DataUnavailableError("Missing T1")
            return [(15.0, 71.8, {"hs": 1.0, "stp": 0.01, "spr": 0.25, "hsea_initial": 1.0, "hsea_final": 1.0, "wind_speed_kmh": 10.0, "wind_dir_deg": 180, "current_speed_ms": 0.5, "current_dir_deg": 90})]
        mock_load.side_effect = side_effect
        
        from datetime import datetime
        try:
            ForecastDataService.get_environment(15.0, 71.8, datetime(2026, 8, 27, 13, 0, 0))
            assert False, "Should have raised DataUnavailableError"
        except DataUnavailableError:
            pass
    print("Test 4 passed.")

def test_p0_missing_bsi_inputs():
    """Test 5: Missing BSI inputs"""
    print("Running Test 5...")
    from app.api.services.forecast_data import ForecastDataService
    from datetime import datetime
    
    with patch("app.api.services.forecast_data.ForecastDataService.load_grid") as mock_load:
        mock_load.return_value = [(15.0, 71.8, {"hs": 1.0, "spr": 0.25, "hsea_initial": 1.0, "hsea_final": 1.0, "wind_speed_kmh": 10.0, "wind_dir_deg": 180, "current_speed_ms": 0.5, "current_dir_deg": 90})]
        
        try:
            ForecastDataService.get_environment(15.0, 71.8, datetime(2026, 8, 27, 12, 0, 0))
            assert False, "Should have raised DataUnavailableError"
        except DataUnavailableError as e:
            assert "Missing required environmental variable 'stp'" in str(e)
    print("Test 5 passed.")

def test_p0_wfs_failure():
    """Test 6: WFS Failure"""
    print("Running Test 6...")
    with patch("app.api.services.incois_geoserver.INCOISGeoServerClient.get_pfz_lines_wfs") as mock_wfs:
        mock_wfs.side_effect = Exception("Network timeout")
        
        res = client.post("/api/trip/analyze", json={
            "start": {"lat": 15.0, "lon": 71.8},
            "departure_time": "2026-08-27T12:00:00Z"
        })
        
        assert res.status_code == 200
        assert res.json()["decision"] == "DATA_UNAVAILABLE"
    print("Test 6 passed.")

def test_p0_determinism():
    """Test 7: Determinism"""
    print("Running Test 7...")
    from app.api.services.pfz_routing import PFZRoutingService
    route_a = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    route_b = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    assert route_a == route_b
    print("Test 7 passed.")

if __name__ == "__main__":
    test_p0_api_contract()
    test_p0_speed_sensitivity()
    test_p0_temporal_sensitivity()
    test_p0_missing_t1()
    test_p0_missing_bsi_inputs()
    test_p0_wfs_failure()
    test_p0_determinism()
    print("All P0 semantic tests passed successfully!")
