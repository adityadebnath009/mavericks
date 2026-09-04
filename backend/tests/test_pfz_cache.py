import time
import os
import json
from unittest.mock import patch

from app.api.services.incois_geoserver import INCOISGeoServerClient, WFS_CACHE_PATH

def run_tests():
    print("Running PFZ Caching Tests...\n")
    
    # Ensure a fresh mock cache file exists
    mock_data = {"type": "FeatureCollection", "features": [], "test_flag": "cached_data"}
    os.makedirs(os.path.dirname(WFS_CACHE_PATH), exist_ok=True)
    with open(WFS_CACHE_PATH, "w") as f:
        json.dump(mock_data, f)
        
    # Set the mtime to exactly 1 hour ago
    one_hour_ago = time.time() - 3600
    os.utime(WFS_CACHE_PATH, (one_hour_ago, one_hour_ago))
    
    # Test 1: Fresh cache (under 12 hours) should NOT make network requests
    with patch("requests.get") as mock_get:
        result = INCOISGeoServerClient.get_pfz_lines_wfs()
        
        if result.get("test_flag") == "cached_data" and not mock_get.called:
            print("✅ Test 1 Passed: Recent cache used (Age: 1 hr). Zero network requests made.")
        else:
            print(f"❌ Test 1 Failed: Network hit occurred or wrong data. Called: {mock_get.called}")

    # Set the mtime to 14 hours ago (stale cache)
    stale_time = time.time() - (14 * 3600)
    os.utime(WFS_CACHE_PATH, (stale_time, stale_time))

    # Test 2: Stale cache should TRIGGER network request
    with patch("requests.get") as mock_get:
        class MockResponse:
            status_code = 200
            def json(self): return {"type": "FeatureCollection", "features": [], "test_flag": "live_data"}
        mock_get.return_value = MockResponse()
        
        result = INCOISGeoServerClient.get_pfz_lines_wfs()
        
        if result.get("test_flag") == "live_data" and mock_get.called:
            print("✅ Test 2 Passed: Stale cache (Age: 14 hr) correctly bypassed. Live network fetch triggered.")
        else:
            print(f"❌ Test 2 Failed: Network fetch logic failed.")
            
    # Clean up mock file so we don't break actual app execution
    if os.path.exists(WFS_CACHE_PATH):
        os.remove(WFS_CACHE_PATH)

if __name__ == "__main__":
    run_tests()
