from datetime import datetime, timedelta
from app.api.services.forecast_data import ForecastDataService
from app.core.exceptions import DataUnavailableError

def test_resolve_forecast_time_valid():
    # Baseline is 2026-08-26 00:00:00
    dep_time = "2026-08-26T12:00:00Z"
    elapsed = ForecastDataService.resolve_forecast_time(dep_time)
    assert elapsed == 12.0

def test_resolve_forecast_time_invalid_format():
    try:
        ForecastDataService.resolve_forecast_time("invalid_date")
        assert False, "Should raise DataUnavailableError"
    except DataUnavailableError as e:
        assert "Invalid departure_time format" in str(e)

def test_resolve_forecast_time_out_of_bounds():
    try:
        # Before baseline
        ForecastDataService.resolve_forecast_time("2026-08-25T12:00:00Z")
        assert False, "Should raise DataUnavailableError"
    except DataUnavailableError:
        pass
        
    try:
        # After 72 hours
        ForecastDataService.resolve_forecast_time("2026-08-29T01:00:00Z")
        assert False, "Should raise DataUnavailableError"
    except DataUnavailableError:
        pass

def test_get_environment_out_of_spatial_bounds():
    # Use a coordinate very far away (e.g., Antarctica)
    lat = -80.0
    lon = 0.0
    timestamp = datetime(2026, 8, 26, 12, 0, 0)
    
    try:
        ForecastDataService.get_environment(lat, lon, timestamp)
        assert False, "Should raise DataUnavailableError for spatial out of bounds"
    except DataUnavailableError as e:
        assert "out of bounds" in str(e)

def test_get_environment_temporal_interpolation():
    # Use a coordinate we know is probably in the cache
    # The cache usually covers the Bay of Bengal / Arabian Sea
    # Let's mock load_grid instead of depending on actual cache files for unit test stability
    
    original_load = ForecastDataService.load_grid
    
    # Mock
    def mock_load_grid(day, hour):
        # Return dummy node near 15.0, 75.0
        return [
            (15.0, 75.0, {
                "hs": float(hour), # hs = hour 
                "bsi": 1
            })
        ]
        
    ForecastDataService.load_grid = mock_load_grid
    
    try:
        # 2026-08-26 01:30:00 -> elapsed = 1.5 hrs
        # t0 = 0 hrs (hs=0), t1 = 3 hrs (hs=3)
        # Interpolation fraction = 0.5
        # Expected hs = 1.5
        timestamp = datetime(2026, 8, 26, 1, 30, 0)
        env = ForecastDataService.get_environment(15.0, 75.0, timestamp)
        assert env.wave_height_m == 1.5
        assert env.bsi == 1
    finally:
        ForecastDataService.load_grid = original_load
        
if __name__ == "__main__":
    test_resolve_forecast_time_valid()
    test_resolve_forecast_time_invalid_format()
    test_resolve_forecast_time_out_of_bounds()
    test_get_environment_out_of_spatial_bounds()
    test_get_environment_temporal_interpolation()
    print("ALL FORECAST DATA TESTS PASSED")
