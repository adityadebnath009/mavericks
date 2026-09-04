import os
import sys
import time
import requests
import concurrent.futures
from unittest.mock import patch, MagicMock

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.api.services.incois_client import INCOISClient, CircuitBreaker, DataUnavailableError

# Fake clock for deterministic testing
_current_time = 1000.0
def fake_clock():
    return _current_time

def run_smoke5():
    global _current_time
    print("Starting Smoke 5: Circuit Breaker Recovery on OPeNDAP Layer")
    print("-" * 60)
    
    # 1. Setup isolated client and breaker
    breaker = CircuitBreaker(threshold=3, recovery_timeout=10, clock=fake_clock)
    client = INCOISClient()
    client.circuit = breaker
    
    # Track mock metrics
    upstream_calls = 0
    
    # We mock requests.adapters.HTTPAdapter.send which is super().send() 
    # from IncoisHTTPAdapter's perspective.
    original_send = requests.adapters.HTTPAdapter.send
    def mock_send(self, request, **kwargs):
        nonlocal upstream_calls
        upstream_calls += 1
        
        # We simulate a 502 Bad Gateway to cause a failure when needed,
        # or a 200 OK for success.
        if hasattr(mock_send, "should_fail") and mock_send.should_fail:
            # Pydap raises HTTPError on 5xx
            response = requests.Response()
            response.status_code = 502
            return response
        
        response = requests.Response()
        response.status_code = 200
        return response

    with patch("requests.adapters.HTTPAdapter.send", new=mock_send):
        
        import random
        def make_request():
            try:
                client.session.get(f"https://www.incois.gov.in/test?rand={random.random()}")
                return "SUCCESS"
            except DataUnavailableError as e:
                print(f"DEBUG: Caught DataUnavailableError: {e}")
                if "OPEN" in str(e):
                    return "REJECTED"
                return "ERROR"
            except Exception as e:
                print(f"DEBUG: Caught other exception: {type(e)} - {e}")
                return "ERROR"
        
        print("PHASE: Failure accumulation")
        mock_send.should_fail = True
        
        res1 = make_request()
        assert res1 == "ERROR", "Should return ERROR due to 502"
        assert breaker.failures == 1
        assert breaker.state == "CLOSED"
        
        res2 = make_request()
        assert breaker.failures == 2
        assert breaker.state == "CLOSED"
        
        res3 = make_request()
        assert breaker.failures >= 3
        assert breaker.state == "OPEN"
        print("  ✓ failures increments to 3, state = OPEN")
        
        print("PHASE: Open rejection")
        calls_before = upstream_calls
        res4 = make_request()
        assert res4 == "REJECTED"
        assert upstream_calls == calls_before
        print("  ✓ Next request rejected; mock call count unchanged")
        
        print("PHASE: Half-open & Herd protection")
        # Advance clock to trigger half-open
        _current_time += 15.0
        
        results = []
        calls_before_herd = upstream_calls
        
        mock_send.should_fail = False
        
        def mock_send_slow(self, request, **kwargs):
            nonlocal upstream_calls
            upstream_calls += 1
            if hasattr(mock_send, "should_fail") and mock_send.should_fail:
                response = requests.Response()
                response.status_code = 502
                return response
            
            time.sleep(0.1) # Simulate network delay to hold the lock open
            response = requests.Response()
            response.status_code = 200
            return response
            
        with patch("requests.adapters.HTTPAdapter.send", new=mock_send_slow):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                for f in concurrent.futures.as_completed(futures):
                    results.append(f.result())
                
        successes = results.count("SUCCESS")
        rejections = results.count("REJECTED")
        actual_calls = upstream_calls - calls_before_herd
        
        assert successes == 1, f"Expected exactly 1 probe to succeed, got {successes}"
        assert rejections == 4, f"Expected 4 requests to be rejected, got {rejections}"
        assert actual_calls == 1, f"Expected 1 upstream call, got {actual_calls}"
        print("  ✓ exactly one probe, remaining calls rejected, 1 mock call made")
        
        print("PHASE: Successful recovery")
        assert breaker.failures == 0
        assert breaker.state == "CLOSED"
        print("  ✓ failures = 0, state = CLOSED")
        
        print("PHASE: Post-recovery")
        calls_before_post = upstream_calls
        res_post = make_request()
        assert res_post == "SUCCESS"
        assert upstream_calls == calls_before_post + 1
        assert breaker.state == "CLOSED"
        print("  ✓ Fire request; mock call succeeds, state remains CLOSED")
        
        print("PHASE: Failed recovery")
        # Fail 3x -> OPEN
        mock_send.should_fail = True
        make_request()
        make_request()
        make_request()
        assert breaker.state == "OPEN"
        
        # Advance clock -> HALF_OPEN
        _current_time += 15.0
        
        calls_before_fail_probe = upstream_calls
        res_fail_probe = make_request()
        assert res_fail_probe == "ERROR" 
        assert upstream_calls == calls_before_fail_probe + 1
        assert breaker.state == "OPEN"
        print("  ✓ Fail 3x -> OPEN. Advance clock -> HALF_OPEN. Probe fails -> state = OPEN")
        
        print("PHASE: Post-failed recovery")
        calls_before_post_fail = upstream_calls
        res_post_fail = make_request()
        assert res_post_fail == "REJECTED"
        assert upstream_calls == calls_before_post_fail
        print("  ✓ Fire request; no mock call made (rejected)")

        print("-" * 60)
        print("Smoke 5 Certification: ALL PASSED")

if __name__ == "__main__":
    run_smoke5()
