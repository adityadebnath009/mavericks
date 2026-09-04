from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_analyze_endpoint():
    payload = {
        "start": {"lat": 15.0, "lon": 75.0},
        "departure_time": "2026-08-26T12:00:00Z",
        "vessel": {"beam_m": 4.0, "length_m": 12.0, "cruising_speed_kn": 12.0}
    }
    
    # We must mock geofence and INCOIS WFS otherwise it reaches out to live services
    from unittest.mock import patch
    with patch("app.api.services.trip_decision.INCOISGeoServerClient.get_pfz_lines_wfs") as mock_wfs, \
         patch("app.api.services.pfz_routing.evaluate_geofence_offline") as mock_gf, \
         patch("app.api.services.trip_decision.evaluate_geofence_offline") as mock_gf2:
        
        mock_wfs.return_value = {
            "features": [{"id": "PFZ-1", "geometry": {"type": "LineString", "coordinates": [[75.1, 15.1], [75.2, 15.2]]}}]
        }
        mock_gf.return_value = {"is_inside_eez": True, "is_inside_mpa": False}
        mock_gf2.return_value = {"is_inside_eez": True, "is_inside_mpa": False}
        
        # We also mock load_grid
        from app.api.services.forecast_data import ForecastDataService
        original_load = ForecastDataService.load_grid
        def mock_load_grid(d, h):
            return [(15.0, 75.0, {"hs": 0.5, "bsi": 0}), (15.1, 75.1, {"hs": 0.5, "bsi": 0}), (15.2, 75.2, {"hs": 0.5, "bsi": 0})]
            
        ForecastDataService.load_grid = mock_load_grid
        
        try:
            response = client.post("/api/trip/analyze", json=payload)
            if response.status_code != 200:
                print(response.json())
            assert response.status_code == 200
            
            data = response.json()
            assert "decision" in data
            assert data["decision"] in ["RECOMMENDED", "CAUTION", "REJECTED_NO_SAFE_ROUTE"]
            print(json.dumps(data, indent=2))
            print("✓ API test passed")
        finally:
            ForecastDataService.load_grid = original_load

if __name__ == "__main__":
    test_analyze_endpoint()
