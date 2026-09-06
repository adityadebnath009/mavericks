import pytest
from unittest import mock
import datetime
from app.api.endpoints.safety import get_safety_assessment
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

@mock.patch('app.api.endpoints.safety.check_geofence_status', return_value={"is_inside_eez": True, "distance_to_border_km": 100})
@mock.patch('app.api.services.marine_forecast.MarineForecastService._fetch_open_meteo_with_cache')
def test_weather_mode_missing_data_handling(mock_fetch, mock_geo):
    # Simulate an Open-Meteo failure
    mock_fetch.side_effect = Exception("Open-Meteo Connection Timeout")
    try:
        response = get_safety_assessment(lat=15.0, lon=73.0, beam=4.0, day=1, hour=12, db=None)
        pytest.fail("Expected HTTP Exception or Graceful Failure")
    except Exception as e:
        # API correctly handles failure without fabricating a mock 0-7 score
        assert "Open-Meteo Connection Timeout" in str(e)

@mock.patch('app.api.endpoints.safety.check_geofence_status', return_value={"is_inside_eez": True, "distance_to_border_km": 100})
@mock.patch('app.api.services.marine_forecast.OpenMeteoProvider.extract_forecast')
@mock.patch('app.api.services.marine_forecast.MarineForecastService._fetch_open_meteo_with_cache')
def test_weather_mode_schema_compliance(mock_fetch, mock_extract, mock_geo):
    mock_fetch.return_value = ({}, {}, False, 0)
    # Return valid mock environment data
    mock_extract.return_value = (
        {"wave_height_m": 2.0, "wind_speed_ms": 15.0, "wave_period_s": 5.0}, 
        {"snapshots": [{"time": datetime.datetime.utcnow(), "wave_height_m": 2.0, "wind_speed_ms": 15.0}]}
    )
    
    response = get_safety_assessment(lat=15.0, lon=73.0, beam=4.0, day=1, hour=12, db=None)
    
    # 1. BSI Score is within 0-100
    assert 0 <= response["severity_score"] <= 100
    
    # 2. Frozen schema elements are present
    assert "confidence" in response
    assert "hazards" in response
    assert "available_hazards" in response
    assert "unavailable_hazards" in response
    assert "daily_peaks" in response
    
    # 3. No legacy SVAS nomenclature
    assert "SVAS" not in str(response)

