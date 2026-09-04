import sys
sys.path.insert(0, "backend")
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
client = TestClient(app)

with patch("app.api.services.forecast_data.ForecastDataService.get_environment") as mock_env, \
     patch("app.api.services.forecast_data.ForecastDataService.get_grid_nodes") as mock_nodes, \
     patch("app.api.services.pfz_routing.evaluate_geofence_offline") as mock_geo, \
     patch("app.api.services.orca_bsi_engine.OrcaBsiEngine.evaluate") as mock_eval:
    
    mock_nodes.return_value = [(15.2, 73.8), (15.4, 74.0), (15.7, 74.2)]
    mock_env_instance = MagicMock()
    mock_env_instance.wave_height_m = 1.0
    mock_env_instance.wind_speed_kmh = 10.0
    mock_env_instance.wind_direction_deg = 180
    mock_env_instance.current_speed_ms = 0.5
    mock_env_instance.current_direction_deg = 180
    mock_env.return_value = mock_env_instance
    
    mock_geo.return_value = {"is_inside_eez": True, "is_inside_mpa": False, "distance_to_border_km": 10.0}
    mock_eval.return_value = {"bsi": 2, "severity_score": 40}
    
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.json())
    print("EVAL CALLED:", mock_eval.called)
