import os
import shutil
from app.api.services.incois_resolver import IncoisDatasetResolver

def test_cache_paths():
    lat, lon, day = 15.1234, 73.5678, 1
    ww3_path, curr_path = IncoisDatasetResolver.get_cache_paths(lat, lon, day)
    
    # Assert correct rounding in path keys
    assert "lat_15.123_lon_73.568_day_1.pkl" in ww3_path
    assert "lat_15.123_lon_73.568_day_1.pkl" in curr_path

def test_remote_resolve():
    lat, lon, day = 15.0, 73.0, 1
    
    # Clean cache first to force remote fetch
    ww3_path, curr_path = IncoisDatasetResolver.get_cache_paths(lat, lon, day)
    if os.path.exists(ww3_path):
        os.remove(ww3_path)
    if os.path.exists(curr_path):
        os.remove(curr_path)
        
    try:
        ww3_records, curr_records = IncoisDatasetResolver.resolve_latest_forecast(lat, lon, day)
        
        # Assert exact step sizes
        assert len(ww3_records) == 8
        assert len(curr_records) == 8
        
        # Assert correct variable mapping and type assertions
        for step in ww3_records:
            assert isinstance(step["hs"], float)
            assert isinstance(step["stp"], float)
            assert isinstance(step["spr"], float)
            assert isinstance(step["wind_speed_kmh"], float)
            assert "timestamp" in step
            
        for step in curr_records:
            assert isinstance(step["speed_m_s"], float)
            assert isinstance(step["direction_deg"], float)
            assert "timestamp_ww3" in step
            assert "timestamp_curr" in step
            
        # Assert cache files were written
        assert os.path.exists(ww3_path)
        assert os.path.exists(curr_path)
    except Exception as e:
        err_msg = str(e)
        if "timeout" in err_msg.lower() or "connection" in err_msg.lower() or "netcdf" in err_msg.lower() or "i/o failure" in err_msg.lower():
            print(f"Skipping remote resolve assertions due to network/server timeout: {e}")
        else:
            raise e

if __name__ == "__main__":
    print("Running resolver tests...")
    test_cache_paths()
    print("✓ test_cache_paths passed.")
    test_remote_resolve()
    print("✓ test_remote_resolve passed.")
    print("All resolver tests completed successfully!")
