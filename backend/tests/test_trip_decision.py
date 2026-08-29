import os
import sys
import json
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.trip_decision import TripDecisionEngine

def get_mock_db():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    return session

# 1. Test Phase 1: Scalar, Vector, and Angle Interpolation
def test_temporal_forecast_resolver_interpolation():
    loaded_grids = {
        (1, 0): {
            (19.0, 72.5): {
                "bsi": 1, "hs": 1.0, "wind_speed_kmh": 10.0, "current_speed_ms": 0.2,
                "wind_dir_deg": 10.0, "current_dir_deg": 90.0,
                "stp": 0.01, "spr": 0.2, "hsea_initial": 0.5, "hsea_final": 0.5
            }
        },
        (1, 3): {
            (19.0, 72.5): {
                "bsi": 2, "hs": 2.0, "wind_speed_kmh": 20.0, "current_speed_ms": 0.4,
                "wind_dir_deg": 20.0, "current_dir_deg": 100.0,
                "stp": 0.02, "spr": 0.3, "hsea_initial": 0.9, "hsea_final": 0.9
            }
        }
    }

    props = PFZRoutingService.get_interpolated_properties(19.0, 72.5, 1.5, loaded_grids)

    assert abs(props["hs"] - 1.5) < 1e-4
    assert abs(props["wind_speed_kmh"] - 15.0) < 1e-4
    assert props["current_speed_ms"] > 0.0
    assert 10.0 < props["wind_dir_deg"] < 20.0
    assert props["bsi"] >= 0

# 2. Test Phase 2: Time-Dependent Dijkstra Search
def test_time_dependent_pfz_routing():
    db = get_mock_db()
    with patch('app.api.services.pfz_routing.json.load') as mock_json_load, \
         patch('app.api.services.pfz_routing.os.path.exists', return_value=True), \
         patch('builtins.open', MagicMock()):
        
        mock_json_load.return_value = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"center_lat": 19.0, "center_lon": 72.5, "bsi": 0, "hs": 1.0, "wind_speed_kmh": 10.0, "current_speed_ms": 0.1, "wind_dir_deg": 10, "current_dir_deg": 90, "stp":0.01,"spr":0.2,"hsea_initial":0.5,"hsea_final":0.5}},
                {"properties": {"center_lat": 19.5, "center_lon": 72.5, "bsi": 0, "hs": 1.0, "wind_speed_kmh": 10.0, "current_speed_ms": 0.1, "wind_dir_deg": 10, "current_dir_deg": 90, "stp":0.01,"spr":0.2,"hsea_initial":0.5,"hsea_final":0.5}}
            ]
        }

        route_res = PFZRoutingService.calculate_optimal_route(
            start_lat=19.0, start_lon=72.5,
            end_lat=19.5, end_lon=72.5,
            beam_m=3.0, day=1, hour=0,
            db=db, departure_time="2026-08-26T00:00:00Z"
        )

        assert "route_coords" in route_res
        print("DEBUG route_res:", route_res)
        assert "snapshots" in route_res
        assert len(route_res["snapshots"]) > 0
        assert route_res["snapshots"][0]["arrival_time"] == "00:00"
    db.close()

# 3. Test Phase 3, 4 & 5: Orchestrated Trip Evaluation & Safety Windows
def test_pfz_candidate_evaluation_and_ranking():
    db = get_mock_db()
    dummy_pfzs = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "PFZ-MOCK-1",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[72.5, 19.0], [72.6, 19.0]]
                }
            }
        ]
    }

    with patch('app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs', return_value=dummy_pfzs), \
         patch('app.api.services.trip_decision.evaluate_geofence_offline') as mock_gf, \
         patch('app.api.services.pfz_routing.PFZRoutingService.calculate_optimal_route') as mock_route:
        
        mock_gf.return_value = {"is_inside_eez": True, "is_inside_mpa": False, "mpa_name": None}
        mock_route.return_value = {
            "route_coords": [[72.5, 19.0]],
            "straight_coords": [[72.5, 19.0]],
            "summary": {"distance_km": 0.0, "travel_time_hours": 0.0, "max_bsi": 0, "overall_risk": "LOW", "avoided_hazards": []},
            "alternate_route": {"current_status": "neutral"},
            "comparison": {"recommended": "Route A", "reason": "Mock route"},
            "snapshots": [{"arrival_time": "00:00", "wave_height_m": 0.5, "wind_speed_kmh": 10.0, "current_speed_ms": 0.1, "bsi": 0}]
        }

        analysis = TripDecisionEngine.analyze_trip(
            start_lat=19.0, start_lon=72.5,
            departure_time="2026-08-26T00:00:00Z",
            beam_m=3.0, length_m=10.0, cruising_speed_kn=8.0,
            db=db
        )

        assert analysis["decision"] == "RECOMMENDED"
        assert analysis["recommended_pfz"]["id"] == "PFZ-MOCK-1"
        assert len(analysis["decision_reasons"]) > 0
    db.close()

# 4. Test Phase 7: Spatio-Temporal Wave-Jump Validation Test
def test_dynamic_temporal_wave_jump_routing():
    db = get_mock_db()
    
    def mock_interpolate(lat, lon, t_current, loaded_grids):
        if t_current >= 5.0:
            return {
                "bsi": 4, "hs": 3.5, "wind_speed_kmh": 25.0, "current_speed_ms": 0.3,
                "wind_dir_deg": 10, "current_dir_deg": 90, "stp": 0.02, "spr": 0.2,
                "hsea_initial": 0.8, "hsea_final": 0.8
            }
        else:
            return {
                "bsi": 1, "hs": 1.0, "wind_speed_kmh": 12.0, "current_speed_ms": 0.1,
                "wind_dir_deg": 10, "current_dir_deg": 90, "stp": 0.01, "spr": 0.2,
                "hsea_initial": 0.4, "hsea_final": 0.4
            }

    dummy_pfzs = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "PFZ-STORM-1",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[72.5, 19.5], [72.6, 19.5]]
                }
            }
        ]
    }

    with patch('app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs', return_value=dummy_pfzs), \
         patch('app.api.services.trip_decision.evaluate_geofence_offline', return_value={"is_inside_eez": True, "is_inside_mpa": False}), \
         patch('app.api.services.pfz_routing.PFZRoutingService.get_interpolated_properties', side_effect=mock_interpolate):

        # 06:00 Departure (Elapsed 0.0 hrs) -> RECOMMENDED
        res_early = TripDecisionEngine.analyze_trip(
            start_lat=19.0, start_lon=72.5,
            departure_time="2026-08-26T00:00:00Z",
            beam_m=2.0, length_m=10.0, cruising_speed_kn=8.0,
            db=db
        )
        assert res_early["decision"] == "RECOMMENDED"

        # 08:00 Departure (Elapsed 2.0 hrs) -> REJECTED (due to 3.5m waves at arrival)
        res_late = TripDecisionEngine.analyze_trip(
            start_lat=19.0, start_lon=72.5,
            departure_time="2026-08-26T02:00:00Z",
            beam_m=2.0, length_m=10.0, cruising_speed_kn=8.0,
            db=db
        )
        assert res_late["decision"] == "REJECTED"
        assert "Dangerous arrival state" in res_late["alternatives"][0]["reason"]
    db.close()

def test_routing_with_zero_current():
    db = get_mock_db()
    with patch('app.api.services.pfz_routing.json.load') as mock_json_load, \
         patch('app.api.services.pfz_routing.os.path.exists', return_value=True), \
         patch('builtins.open', MagicMock()):
        
        mock_json_load.return_value = {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"center_lat": 19.0, "center_lon": 72.5, "bsi": 0, "hs": 1.0, "wind_speed_kmh": 10.0, "current_speed_ms": 0.0, "wind_dir_deg": 10, "current_dir_deg": 90, "stp":0.01,"spr":0.2,"hsea_initial":0.5,"hsea_final":0.5}},
                {"properties": {"center_lat": 19.5, "center_lon": 72.5, "bsi": 0, "hs": 1.0, "wind_speed_kmh": 10.0, "current_speed_ms": 0.0, "wind_dir_deg": 10, "current_dir_deg": 90, "stp":0.01,"spr":0.2,"hsea_initial":0.5,"hsea_final":0.5}}
            ]
        }

        route_res = PFZRoutingService.calculate_optimal_route(
            start_lat=19.0, start_lon=72.5,
            end_lat=19.5, end_lon=72.5,
            beam_m=3.0, day=1, hour=0,
            db=db, departure_time="2026-08-26T00:00:00Z"
        )

        assert route_res["summary"]["travel_time_hours"] > 0
        for snap in route_res["snapshots"]:
            assert snap["current_speed_ms"] == 0.0
            assert snap["current_parallel_ms"] == 0.0
    db.close()

def test_routing_extreme_wind_rejection():
    db = get_mock_db()
    
    def mock_interpolate_wind(lat, lon, t_current, loaded_grids):
        return {
            "bsi": 5, "hs": 1.0, "wind_speed_kmh": 85.0, "current_speed_ms": 0.1,
            "wind_dir_deg": 10, "current_dir_deg": 90, "stp": 0.01, "spr": 0.2,
            "hsea_initial": 0.5, "hsea_final": 0.5
        }

    dummy_pfzs = {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "PFZ-WINDY-1",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[72.5, 19.5], [72.6, 19.5]]
                }
            }
        ]
    }

    with patch('app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs', return_value=dummy_pfzs), \
         patch('app.api.services.trip_decision.evaluate_geofence_offline', return_value={"is_inside_eez": True, "is_inside_mpa": False}), \
         patch('app.api.services.pfz_routing.PFZRoutingService.get_interpolated_properties', side_effect=mock_interpolate_wind):

        res = TripDecisionEngine.analyze_trip(
            start_lat=19.0, start_lon=72.5,
            departure_time="2026-08-26T00:00:00Z",
            beam_m=2.0, length_m=10.0, cruising_speed_kn=8.0,
            db=db
        )
        assert res["decision"] == "REJECTED"
    db.close()

def test_empty_pfz_advisory_handling():
    db = get_mock_db()
    with patch('app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs', return_value={"type": "FeatureCollection", "features": []}):
        res = TripDecisionEngine.analyze_trip(
            start_lat=19.0, start_lon=72.5,
            departure_time="2026-08-26T00:00:00Z",
            beam_m=3.0, length_m=10.0, cruising_speed_kn=8.0,
            db=db
        )
        assert res["decision"] == "REJECTED"
        assert "No active INCOIS PFZ Advisory" in res["reason"]
    db.close()

if __name__ == "__main__":
    print("Running trip decision tests...")
    test_temporal_forecast_resolver_interpolation()
    print("✓ test_temporal_forecast_resolver_interpolation passed.")
    test_time_dependent_pfz_routing()
    print("✓ test_time_dependent_pfz_routing passed.")
    test_pfz_candidate_evaluation_and_ranking()
    print("✓ test_pfz_candidate_evaluation_and_ranking passed.")
    test_dynamic_temporal_wave_jump_routing()
    print("✓ test_dynamic_temporal_wave_jump_routing passed.")
    test_routing_with_zero_current()
    print("✓ test_routing_with_zero_current passed.")
    test_routing_extreme_wind_rejection()
    print("✓ test_routing_extreme_wind_rejection passed.")
    test_empty_pfz_advisory_handling()
    print("✓ test_empty_pfz_advisory_handling passed.")
    print("All trip decision tests passed!")

