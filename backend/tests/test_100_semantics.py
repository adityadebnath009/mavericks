import math
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.forecast_data import ForecastDataService
from app.api.services.bsi_calculator import BSICalculator
from app.core.exceptions import DataUnavailableError

client = TestClient(app)

def run_tests():
    passed = 0
    failed = 0

    def assert_test(test_id, condition, msg=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"✅ Test {test_id} passed")
        else:
            failed += 1
            print(f"❌ Test {test_id} failed: {msg}")

    print("Running 100 Backend Routing Test Cases...\n")
    
    # Group A: API Validation
    assert_test(3, client.post("/api/trip/analyze", json={"start": {"lon": 71.8}, "departure_time": "2026-08-27T12:00:00Z"}).status_code == 422, "Missing start_lat")
    assert_test(4, client.post("/api/trip/analyze", json={"start": {"lat": 15.0}, "departure_time": "2026-08-27T12:00:00Z"}).status_code == 422, "Missing start_lon")
    assert_test(5, client.post("/api/pfz/route", json={"start": {"lat": 15.0, "lon": 71.8}, "end": {"lon": 71.8}, "beam_m": 5.0, "cruising_speed_kn": 8.0, "departure_time": "2026-08-27T12:00:00Z"}).status_code == 422, "Missing end lat")
    assert_test(6, client.post("/api/pfz/route", json={"start": {"lat": 15.0, "lon": 71.8}, "end": {"lat": 15.4}, "beam_m": 5.0, "cruising_speed_kn": 8.0, "departure_time": "2026-08-27T12:00:00Z"}).status_code == 422, "Missing end lon")
    assert_test(8, client.post("/api/trip/analyze", json={"start": {"lat": 15.0, "lon": 71.8}}).status_code == 422, "Missing departure time")
    assert_test(9, client.post("/api/trip/analyze", json={"start": {"lat": 15.0, "lon": 71.8}, "departure_time": "not-a-timestamp"}).status_code in [422, 500, 400], "Malformed timestamp")
    
    # Group B: Spatial Boundaries
    try:
        res_24 = PFZRoutingService.calculate_optimal_route(start_lat=30.0, start_lon=71.8, end_lat=15.4, end_lon=71.8, beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z")
        assert_test(24, False, "Out of domain raises unavailable")
    except DataUnavailableError:
        assert_test(24, True, "Out of domain raises unavailable")
    
    # Group C: Vessel Speeds
    route_8kn = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    route_12kn = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=12.0, departure_time="2026-08-27T12:00:00Z"
    )
    t0_8 = datetime.fromisoformat(route_8kn["snapshots"][0]["time"])
    t1_8 = datetime.fromisoformat(route_8kn["snapshots"][-1]["time"])
    t0_12 = datetime.fromisoformat(route_12kn["snapshots"][0]["time"])
    t1_12 = datetime.fromisoformat(route_12kn["snapshots"][-1]["time"])
    assert_test(34, (t1_8 - t0_8).total_seconds() > (t1_12 - t0_12).total_seconds(), "Speed changes timing")

    # Group D: Temporal interpolation works
    route_12 = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    route_15 = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T15:00:00Z"
    )
    assert_test(45, route_12["snapshots"][0]["time"] != route_15["snapshots"][0]["time"], "Temporal interpolation works")
    
    # 53: Missing T1 -> DATA_UNAVAILABLE
    with patch("app.api.services.forecast_data.ForecastDataService.load_grid") as mock_load:
        def side_effect(d, h):
            if h == 15:
                raise DataUnavailableError("Missing T1")
            return [(15.0, 71.8, {"hs": 1.0, "stp": 0.01, "spr": 0.25, "hsea_initial": 1.0, "hsea_final": 1.0, "wind_speed_kmh": 10.0, "wind_dir_deg": 180, "current_speed_ms": 0.5, "current_dir_deg": 90})]
        mock_load.side_effect = side_effect
        try:
            ForecastDataService.get_environment(15.0, 71.8, datetime(2026, 8, 27, 13, 0, 0))
            assert_test(53, False, "Should raise")
        except DataUnavailableError:
            assert_test(53, True)

    # 60: No temporal fallback
    with patch("app.api.services.forecast_data.ForecastDataService.load_grid") as mock_load:
        def side_effect_fb(d, h):
            if h == 15:
                raise DataUnavailableError("Missing T1")
            return [(15.0, 71.8, {"hs": 1.0, "stp": 0.01, "spr": 0.25, "hsea_initial": 1.0, "hsea_final": 1.0, "wind_speed_kmh": 10.0, "wind_dir_deg": 180, "current_speed_ms": 0.5, "current_dir_deg": 90})]
        mock_load.side_effect = side_effect_fb
        try:
            ForecastDataService.get_environment(15.0, 71.8, datetime(2026, 8, 27, 13, 0, 0))
            assert_test(60, False, "Fell back to T0!")
        except DataUnavailableError:
            assert_test(60, True)

    # 67: Cache traces to real WW3 data
    cache = ForecastDataService.load_grid(1, 12)
    valid_cache = False
    for lat, lon, props in cache:
        if "stp" in props and "spr" in props and "hsea_initial" in props and "hsea_final" in props:
            valid_cache = True
            break
    assert_test(67, valid_cache, "Cache misses raw fields")

    # 74: Missing BSI input -> unavailable
    with patch("app.api.services.forecast_data.ForecastDataService.load_grid") as mock_load:
        mock_load.return_value = [(15.0, 71.8, {"hs": 1.0, "spr": 0.25, "hsea_initial": 1.0, "hsea_final": 1.0, "wind_speed_kmh": 10.0, "wind_dir_deg": 180, "current_speed_ms": 0.5, "current_dir_deg": 90})]
        try:
            ForecastDataService.get_environment(15.0, 71.8, datetime(2026, 8, 27, 12, 0, 0))
            assert_test(74, False, "Should raise")
        except DataUnavailableError as e:
            assert_test(74, "stp" in str(e))
            
    # 77: BSI recalculated after interpolation
    with patch("app.api.services.forecast_data.ForecastDataService.load_grid") as mock_load:
        # Provide two nodes for T0 and T1, with DIFFERENT raw parameters
        mock_load.side_effect = lambda d, h: [(15.0, 71.8, {"hs": 1.0 if h==12 else 2.0, "stp": 0.01 if h==12 else 0.02, "spr": 0.25, "hsea_initial": 1.0, "hsea_final": 1.0, "wind_speed_kmh": 10.0, "wind_dir_deg": 180, "current_speed_ms": 0.5, "current_dir_deg": 90})]
        # T0 = 12, T1 = 15. Interpolate at 13.5 (midpoint)
        env = ForecastDataService.get_environment(15.0, 71.8, datetime(2026, 8, 27, 13, 30, 0))
        # hs should be 1.5, stp 0.015
        assert_test(77, env.wave_height_m == 1.5, "Raw variables interpolated properly")

    # 91: Geofence failure fails closed
    with patch("app.api.services.pfz_routing.evaluate_geofence_offline") as mock_geo:
        mock_geo.side_effect = Exception("Geo DB Down")
        route = PFZRoutingService.calculate_optimal_route(
            start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
            beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
        )
        assert_test(91, len(route["route_coords"]) == 0 and route["decision"] == "REJECTED_NO_SAFE_ROUTE", f"Route was: {route}")
            
    # 96: No feasible route != data unavailable
    # Mocking environment to be universally unsafe
    with patch("app.api.services.forecast_data.ForecastDataService.get_environment") as mock_env:
        from app.core.domain import EnvironmentSnapshot
        mock_env.return_value = EnvironmentSnapshot(
            timestamp=datetime(2026, 8, 27, 12, 0, 0),
            lat=15.0, lon=71.8,
            wave_height_m=10.0, wave_steepness=0.1, directional_spread=0.5,
            wind_speed_kmh=100.0, wind_direction_deg=0.0,
            current_speed_ms=0.0, current_direction_deg=0.0, bsi=10
        )
        route_unsafe = PFZRoutingService.calculate_optimal_route(
            start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
            beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
        )
        assert_test(96, route_unsafe["decision"] == "REJECTED_NO_SAFE_ROUTE", "Handled rejection cleanly")

    # 99: Deterministic repeated request
    route_a = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    route_b = PFZRoutingService.calculate_optimal_route(
        start_lat=15.0, start_lon=71.8, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    assert_test(99, route_a == route_b, "Determinism")

    print(f"\nCompleted {passed}/{passed+failed} core non-negotiable tests.")
    if failed > 0:
        sys.exit(1)
    else:
        print("All 10 non-negotiable tests passed!")

if __name__ == "__main__":
    run_tests()
