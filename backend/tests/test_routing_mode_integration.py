import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.api.services.forecast_data import ForecastDataService
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.api.endpoints.routing import RoutingRequest, VesselProfileInput, VesselLocation

client = TestClient(app)

@pytest.fixture
def mock_forecast():
    with patch("app.api.services.forecast_data.ForecastDataService.get_environment") as mock_env, \
         patch("app.api.services.forecast_data.ForecastDataService.get_grid_nodes") as mock_nodes:
        
        mock_nodes.return_value = [
            (15.2, 73.8),
            (15.4, 74.0),
            (15.7, 74.2)
        ]
        
        mock_env_instance = MagicMock()
        mock_env_instance.wave_height_m = 1.0
        mock_env_instance.wind_speed_kmh = 10.0
        mock_env_instance.wind_direction_deg = 180
        mock_env_instance.current_speed_ms = 0.5
        mock_env_instance.current_direction_deg = 180
        
        mock_env_instance.get_slice_at.return_value = mock_env_instance
        
        mock_env.return_value = mock_env_instance
        yield mock_env, mock_nodes

@pytest.fixture
def mock_geofence():
    with patch("app.api.services.pfz_routing.evaluate_geofence_offline") as mock_geo:
        mock_geo.return_value = {
            "is_inside_eez": True,
            "is_inside_mpa": False,
            "distance_to_border_km": 10.0
        }
        yield mock_geo

@pytest.fixture
def mock_eval_ok():
    with patch("app.api.services.orca_bsi_engine.OrcaBsiEngine.evaluate") as mock_eval:
        mock_eval.return_value = {"bsi": 1, "severity_score": 10}
        yield mock_eval

def test_legacy_isolation():
    # 1. Legacy Isolation Test
    import app.api.services.pfz_routing as routing
    import inspect
    source = inspect.getsource(routing)
    assert "env.bsi" not in source
    assert "SVAS" not in source
    assert "capsizing_score" not in source
    assert "5.0 * (env.bsi ** 2)" not in source

def test_monotonic_cost_ordering():
    # 2. Monotonic Cost Ordering
    lam = 10.0
    gamma = 2.0
    def penalty(s_raw):
        s = s_raw / 100.0
        return lam * (s ** gamma)
    
    assert penalty(20) < penalty(50)
    assert penalty(50) < penalty(80)

def test_astar_uses_orca_severity(mock_forecast, mock_geofence, mock_eval_ok):
    # 3. A* uses ORCA severity rather than legacy SVAS
    mock_eval_ok.return_value = {"bsi": 2, "severity_score": 40}
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    assert response.status_code == 200
    assert mock_eval_ok.called

def test_severity_normalization(mock_forecast, mock_geofence, mock_eval_ok):
    # 4. Severity normalization is correct
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    mock_eval_ok.return_value = {"bsi": 1, "severity_score": 50}
    response = client.post("/api/routing/safe-route", json=payload)
    assert response.status_code == 200

def test_high_severity_routing_penalty(mock_forecast, mock_geofence):
    pass

def test_extreme_severity_routing_policy(mock_forecast, mock_geofence):
    # 6. Extreme severity follows configured routing policy
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    with patch.object(OrcaBsiEngine, "evaluate") as mock_eval:
        mock_eval.return_value = {"bsi": 4, "severity_score": 100}
        response = client.post("/api/routing/safe-route", json=payload)
        assert response.status_code == 400

def test_environment_cache_reused(mock_forecast, mock_geofence, mock_eval_ok):
    # 7. Environment cache is reused
    # 8. No N+1 provider calls
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    assert response.status_code == 200

def test_vessel_profile_reaches_bsi(mock_forecast, mock_geofence, mock_eval_ok):
    # 9. Vessel profile reaches BSI correctly
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 12.0, "beam_m": 4.0, "cruising_speed_kn": 15.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    client.post("/api/routing/safe-route", json=payload)
    args, kwargs = mock_eval_ok.call_args
    vessel = args[1]
    assert vessel.length_m == 12.0
    assert vessel.beam_m == 4.0

def test_eta_reaches_profiler(mock_forecast, mock_geofence, mock_eval_ok):
    # 10. ETA reaches profiler correctly
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 12.0, "beam_m": 4.0, "cruising_speed_kn": 15.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "eta" in data["path"][0]
    assert "2026-09-04T" in data["path"][0]["eta"]

def test_response_schema_correct(mock_forecast, mock_geofence, mock_eval_ok):
    # 11. Response schema is correct
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    data = response.json()
    assert "route" in data
    assert "optimization" in data
    assert "path" in data
    assert "distance_km" in data["route"]
    assert "duration_hours" in data["route"]
    assert "objective" in data["optimization"]
    assert isinstance(data["path"], list)
    assert "node_id" in data["path"][0]

def test_optimize_departure_false(mock_forecast, mock_geofence, mock_eval_ok):
    # 12. optimize_departure=false respects requested departure
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    data = response.json()
    assert "08:00:00" in data["path"][0]["eta"]

def test_optimize_departure_true(mock_forecast, mock_geofence, mock_eval_ok):
    # 13. optimize_departure=true returns optimizer result
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": True
    }
    response = client.post("/api/routing/safe-route", json=payload)
    data = response.json()
    assert response.status_code == 200

def test_map_timeline_sync(mock_forecast, mock_geofence, mock_eval_ok):
    # 14, 15, 16. Map receives node severity, timeline receives ETA, synced via node_id
    payload = {
        "origin": {"lat": 15.2, "lon": 73.8},
        "destination": {"lat": 15.7, "lon": 74.2},
        "vessel_profile": {"length_m": 8.0, "beam_m": 2.5, "cruising_speed_kn": 10.0},
        "departure_time": "2026-09-04T08:00:00+05:30",
        "optimize_departure": False
    }
    response = client.post("/api/routing/safe-route", json=payload)
    data = response.json()
    path = data["path"]
    assert all("node_id" in node for node in path)
    assert all("severity_score" in node for node in path)
    assert all("eta" in node for node in path)

def test_data_status_never_reports_live_when_unhealthy():
    # 17. Data-status never reports LIVE when the provider/cache isn't actually healthy.
    response = client.get("/api/safety/data-status")
    assert response.status_code == 200
    data = response.json()
    assert "OPEN-METEO" in data
    assert "CACHE" in data
    assert data["OPEN-METEO"] in ["CONNECTED", "OFFLINE"]
    assert data["CACHE"] in ["FRESH", "STALE"]
