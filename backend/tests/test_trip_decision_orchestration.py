from unittest.mock import patch, MagicMock
from app.api.services.trip_decision import TripDecisionEngine
from app.core.exceptions import DataUnavailableError

def test_no_pfz_found():
    with patch("app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs") as mock_wfs:
        mock_wfs.return_value = {"features": []}
        res = TripDecisionEngine.analyze_trip(15.0, 75.0, "2026-08-26T12:00:00Z", 4.0, 15.0, 10.0, None)
        assert res["decision"] == "REJECTED_NO_SAFE_ROUTE"
        print("✓ test_no_pfz_found passed")

def test_routing_failure_propagation():
    with patch("app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs") as mock_wfs, \
         patch("app.api.services.trip_decision.evaluate_geofence_offline") as mock_gf, \
         patch("app.api.services.trip_decision.PFZRoutingService.calculate_optimal_route") as mock_routing:
         
        mock_wfs.return_value = {
            "features": [{"id": "PFZ-1", "geometry": {"type": "LineString", "coordinates": [[75.1, 15.1], [75.2, 15.2]]}}]
        }
        mock_gf.return_value = {"is_inside_eez": True, "is_inside_mpa": False}
        
        # Test DataUnavailableError propagation
        mock_routing.side_effect = DataUnavailableError("Grid missing")
        res = TripDecisionEngine.analyze_trip(15.0, 75.0, "2026-08-26T12:00:00Z", 4.0, 15.0, 10.0, None)
        assert res["decision"] == "REJECTED_NO_SAFE_ROUTE"
        assert len(res["alternatives"]) == 1
        assert res["alternatives"][0]["status"] == "DATA_UNAVAILABLE"
        print("✓ test_routing_failure_propagation passed")

if __name__ == "__main__":
    test_no_pfz_found()
    test_routing_failure_propagation()
    print("ALL TRIP DECISION TESTS PASSED")
