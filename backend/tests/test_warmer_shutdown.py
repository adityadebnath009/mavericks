import pytest
import time
import threading
from unittest.mock import patch
from app.api.services.cache_warmer import CacheWarmer

def test_cache_warmer_graceful_shutdown():
    """
    Simulates CacheWarmer running while INCOIS HTTP requests are blocked.
    Triggers shutdown_event, expecting the process to cleanly and quickly exit.
    """
    warmer = CacheWarmer()
    
    # Mock raw features so we have actual coords to enrich
    raw_features = {
        "features": [
            {
                "geometry": {
                    "type": "MultiLineString", 
                    "coordinates": [[[75.0, 15.0], [75.1, 15.1]]]
                }
            }
        ]
    }
    
    # We will block the actual requests.get inside INCOISClient
    with patch("app.api.services.incois_geoserver.INCOISGeoServerClient.get_pfz_lines_wfs", return_value=raw_features):
        with patch("requests.Session.get") as mock_http_get:
            
            # Simulate a stuck network that times out gracefully after 2 seconds
            def slow_get(*args, **kwargs):
                time.sleep(2.0)
                raise Exception("Socket timeout")
                
            mock_http_get.side_effect = slow_get
            
            start_time = time.time()
            
            # Start warmer in background thread
            t = threading.Thread(target=warmer._execute_warm_sets, args=("2026-09-03",))
            t.start()
            
            # Wait for tasks to be submitted and ThreadPoolExecutor to start
            time.sleep(0.5)
            
            # Trigger shutdown externally
            warmer.stop()
            
            # The thread must exit well before the network timeout finishes,
            # or wait for the existing network timeout to finish gracefully 
            # but NOT block indefinitely. Since we injected a 2.0s sleep and 
            # bounded timeout, the thread should join quickly.
            t.join(timeout=3.0)
            
            assert not t.is_alive(), "CacheWarmer thread did not shut down gracefully!"
            
            elapsed = time.time() - start_time
            # Should take less than 3 seconds total
            assert elapsed < 3.0, f"Shutdown took too long: {elapsed} seconds"
