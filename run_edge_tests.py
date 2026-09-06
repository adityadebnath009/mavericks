import sys
import datetime
import unittest.mock as mock

from app.api.endpoints.safety import get_safety_assessment

print("=== TEST 1: Open-Meteo API Timeout (2.1 API Failure) ===")
with mock.patch('app.api.services.marine_forecast.MarineForecastService._fetch_open_meteo_with_cache', side_effect=Exception("Open-Meteo Connection Timeout")):
    try:
        # Mock geofence to avoid DB dependency in this unit test
        with mock.patch('app.api.endpoints.safety.check_geofence_status', return_value={"is_inside_eez": True, "distance_to_border_km": 100}):
            response = get_safety_assessment(lat=15.0, lon=73.0, beam=4.0, day=1, hour=12, db=None)
            print("Status: FAILED (Expected exception but got response)")
    except Exception as e:
        print(f"Status: SUCCESS (API gracefully rejected the request as expected)\nError caught: {e}")

