import pytest
import time
import requests
import threading
from unittest.mock import patch, MagicMock

from app.api.services.incois_client import INCOISClient, DataUnavailableError, IncoisHTTPAdapter
import pydap.net

def test_circuit_breaker_behavior():
    client = INCOISClient()
    client.circuit.threshold = 3
    client.limiter.rate = 100  # High rate for fast testing
    
    session = client.get_session()
    
    # Mock the actual send to simulate 500 errors
    with patch("requests.adapters.HTTPAdapter.send") as mock_send:
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_send.return_value = mock_response
        
        # 1. Hit threshold (3 requests)
        for _ in range(3):
            with pytest.raises(DataUnavailableError, match="INCOIS Server Error"):
                session.get("https://incois.gov.in/test")
                
        assert client.circuit.state == "OPEN"
        assert client.metrics["actual_upstream_requests"] == 3
        
        # 2. Fire 10 worker requests
        for _ in range(10):
            with pytest.raises(DataUnavailableError, match="Circuit Breaker OPEN"):
                session.get("https://incois.gov.in/test")
                
        # 3. Assertions
        assert client.metrics["requests_total"] == 13
        assert client.metrics["actual_upstream_requests"] == 3
        assert client.metrics["circuit_rejections"] == 10

def test_429_backoff_handling():
    client = INCOISClient()
    client.circuit.threshold = 5
    client.circuit.backoff_429 = 10  # 10 second backoff
    client.limiter.rate = 100
    
    session = client.get_session()
    
    with patch("requests.adapters.HTTPAdapter.send") as mock_send:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_send.return_value = mock_response
        
        # 1. Hit 429
        with pytest.raises(DataUnavailableError, match="INCOIS Rate Limit Exceeded"):
            session.get("https://incois.gov.in/test")
            
        assert client.metrics["actual_upstream_requests"] == 1
        assert client.metrics["requests_429"] == 1
        assert client.circuit.backoff_until > time.time()
        
        # 2. Make another request immediately
        with pytest.raises(DataUnavailableError, match="Circuit Breaker OPEN"):
            session.get("https://incois.gov.in/test")
            
        assert client.metrics["actual_upstream_requests"] == 1  # STILL 1
        assert client.metrics["requests_total"] == 2
        
def test_concurrent_worker_rate_limiting():
    client = INCOISClient()
    client.limiter.rate = 5.0  # 5 req/s
    client.limiter.burst = 1
    
    def worker_thread(session_state, results, i):
        try:
            worker_session = pydap.net.restore_session(session_state)
            worker_session.get("https://incois.gov.in/test", timeout=1)
            results[i] = "Success"
        except Exception as e:
            results[i] = str(e)
            
    with client.pydap_transport_protection():
        session_state = pydap.net.extract_session_state(client.get_session())
        
        # Mock requests.adapters.HTTPAdapter.send to just sleep a tiny bit and return 200
        with patch("requests.adapters.HTTPAdapter.send") as mock_send:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_send.return_value = mock_response
            
            threads = []
            results = [None] * 10
            
            start_time = time.time()
            for i in range(10):
                t = threading.Thread(target=worker_thread, args=(session_state, results, i))
                threads.append(t)
                t.start()
                
            for t in threads:
                t.join()
                
            elapsed = time.time() - start_time
            
            assert client.metrics["actual_upstream_requests"] == 10
            # 10 requests at 5 req/s should take at least (10-1) / 5 = 1.8 seconds
            assert elapsed >= 1.8, f"Took {elapsed}, expected >= 1.8"
            print(f"10 concurrent requests took {elapsed:.2f}s")
