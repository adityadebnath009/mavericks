import os
import time
import json
import logging
import threading
import requests
from threading import Lock, Event
from contextlib import contextmanager
from typing import Callable, Any, Optional, Dict, List
from requests.adapters import HTTPAdapter
from app.core.exceptions import DataUnavailableError

logger = logging.getLogger("incois_reliability")

class CircuitBreaker:
    def __init__(self, threshold=5, recovery_timeout=60, backoff_429=15, weight_429=2, clock=time.time):
        self.failures = 0
        self.threshold = threshold
        self.recovery_timeout = recovery_timeout
        self.backoff_429 = backoff_429
        self.weight_429 = weight_429
        self._clock = clock
        
        self.last_failure_time = 0
        self.state = "CLOSED"
        self._lock = Lock()
        self.backoff_until = 0

    def record_failure(self, is_429=False):
        with self._lock:
            now = self._clock()
            self.last_failure_time = now
            if is_429:
                self.backoff_until = now + self.backoff_429
                self.failures += self.weight_429
            else:
                self.failures += 1

            if self.failures >= self.threshold and self.state != "OPEN":
                logger.error("INCOIS_CIRCUIT_OPEN")
                self.state = "OPEN"

    def record_success(self):
        with self._lock:
            if self.state in ["HALF-OPEN", "OPEN"]:
                logger.info("INCOIS_RECOVERED")
            self.failures = 0
            self.state = "CLOSED"
            self.backoff_until = 0

    def allow_request(self) -> bool:
        with self._lock:
            now = self._clock()
            if now < self.backoff_until:
                return False
                
            if self.state == "HALF-OPEN":
                # A probe is currently in flight. Block everyone else until probe succeeds or fails.
                return False
                
            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF-OPEN"
                    logger.info("INCOIS_CIRCUIT_HALF_OPEN_PROBE_DISPATCHED")
                    return True
                return False
            return True

class TokenBucketLimiter:
    def __init__(self, rate=1.0, burst=1):
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = Lock()

    def wait(self):
        while True:
            with self._lock:
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return
            
            logger.info("INCOIS_RATE_LIMIT_WAIT")
            time.sleep(1.0 / self.rate)

class IncoisHTTPAdapter(HTTPAdapter):
    """
    Enforces Rate Limiter and Circuit Breaker on all outbound HTTP requests to INCOIS.
    Mounted globally on pydap worker sessions.
    """
    def __init__(self, incois_client, *args, **kwargs):
        self.client = incois_client
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        from urllib.parse import urlparse
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = (3.0, 10.0)
        hostname = urlparse(request.url).hostname or ""
        is_incois = hostname == "incois.gov.in" or hostname.endswith(".incois.gov.in")
        if not is_incois:
            return super().send(request, **kwargs)

        self.client._increment_metric("requests_total")
        
        if not self.client.circuit.allow_request():
            self.client._increment_metric("circuit_rejections")
            raise DataUnavailableError("INCOIS Circuit Breaker OPEN (Adapter)")
            
        self.client.limiter.wait()
        self.client._increment_metric("actual_upstream_requests")

        try:
            response = super().send(request, **kwargs)
            status = response.status_code
            if status == 429:
                self.client._increment_metric("requests_429")
                self.client._increment_metric("requests_failed")
                self.client.circuit.record_failure(is_429=True)
                raise DataUnavailableError("INCOIS Rate Limit Exceeded (429)")
            elif status >= 500:
                self.client._increment_metric("requests_5xx")
                self.client._increment_metric("requests_failed")
                self.client.circuit.record_failure()
                raise DataUnavailableError(f"INCOIS Server Error ({status})")
            else:
                self.client._increment_metric("requests_success")
                self.client.circuit.record_success()
                return response

        except requests.exceptions.Timeout as e:
            self.client._increment_metric("requests_timeout")
            self.client._increment_metric("requests_failed")
            self.client.circuit.record_failure()
            raise DataUnavailableError("INCOIS Timeout") from e
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            self.client._increment_metric("requests_failed")
            self.client.circuit.record_failure()
            raise DataUnavailableError(f"INCOIS Request Exception: {e}") from e


class INCOISClient:
    """
    Centralized Gateway for all INCOIS traffic.
    Guarantees request coalescing, global rate limiting, and circuit breaking.
    Singleton instance must be shared across the FastAPI application.
    """
    def __init__(self):
        self.circuit = CircuitBreaker()
        self.limiter = TokenBucketLimiter(rate=1.0, burst=1)
        self._inflight = {}
        self._inflight_lock = Lock()
        
        # Centralized Metrics
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "requests_429": 0,
            "requests_5xx": 0,
            "requests_timeout": 0,
            "cache_hits": 0,
            "coalesced_requests": 0,
            "circuit_opens": 0,
            "circuit_rejections": 0,
            "opendap_operations": 0,
            "actual_upstream_requests": 0
        }
        self._metrics_lock = Lock()
        
        self.session = requests.Session()
        adapter = IncoisHTTPAdapter(self)
        self.session.mount("http://incois.gov.in", adapter)
        self.session.mount("https://incois.gov.in", adapter)
        self.session.mount("http://www.incois.gov.in", adapter)
        self.session.mount("https://www.incois.gov.in", adapter)
        
        self._original_restore_session = None

    def _increment_metric(self, key: str, count: int = 1):
        with self._metrics_lock:
            self.metrics[key] += count

    def get(self, url: str, params: dict = None, timeout: int = 15, **kwargs):
        """Standard HTTP GET replacement for requests.get with coalescing."""
        query_str = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items())) if params else ""
        key = f"GET_{url}?{query_str}"
        
        with self._inflight_lock:
            if key in self._inflight:
                event, result_box = self._inflight[key]
                self._increment_metric("coalesced_requests")
                logger.info(f"INCOIS_COALESCED: {key}")
                wait_needed = True
            else:
                event = Event()
                result_box = {"result": None, "error": None}
                self._inflight[key] = (event, result_box)
                wait_needed = False
                
        if wait_needed:
            event.wait()
            if result_box["error"]:
                raise result_box["error"]
            return result_box["result"]
            
        try:
            logger.info(f"INCOIS_UPSTREAM_REQUEST (via get): {key}")
            # Rate limiting and circuit breaking are handled by IncoisHTTPAdapter
            r = self.session.get(url, params=params, timeout=timeout, **kwargs)
            r.raise_for_status()
            
            class CachedResp:
                def __init__(self, content, status):
                    self.content = content
                    self.status_code = status
                    self._json = None
                def json(self):
                    if not self._json:
                        import json
                        self._json = json.loads(self.content)
                    return self._json
            
            res = CachedResp(r.content, r.status_code)
            result_box["result"] = res
            return res
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 500
            # Adapter already records 429 and 5xx. 404 does not trip breaker.
            if status not in [429] and status < 500:
                 pass # other 4xx errors
            # DataUnavailableError could be raised by adapter, so we catch it below
            result_box["error"] = e
            raise e
        except DataUnavailableError as e:
            result_box["error"] = e
            raise e
        except Exception as e:
            result_box["error"] = e
            raise e
        finally:
            event.set()
            with self._inflight_lock:
                self._inflight.pop(key, None)

    def get_session(self) -> requests.Session:
        """
        Returns a requests.Session with the INCOIS protective adapter mounted.
        """
        s = requests.Session()
        adapter = IncoisHTTPAdapter(self)
        s.mount("http://incois.gov.in", adapter)
        s.mount("https://incois.gov.in", adapter)
        s.mount("http://www.incois.gov.in", adapter)
        s.mount("https://www.incois.gov.in", adapter)
        return s

    _pydap_patch_lock = Lock()
    _pydap_patch_count = 0
    _original_build_session = None
    _original_restore_session = None

    @contextmanager
    def pydap_transport_protection(self):
        """
        Context manager to patch pydap.net.build_session and restore_session 
        so that all pydap requests (both sequential main-thread and parallel workers)
        receive the INCOIS protective adapter.
        
        This patch is thread-safe using a reference counter, meaning it will safely
        apply when the first thread enters the context and restore when the last
        thread exits.
        
        WARNING: This is a version-pinned integration boundary specifically for pydap 3.5.10.
        If pydap internals change in future versions, this patch must be updated.
        """
        import pydap.net
        
        with self._pydap_patch_lock:
            if self._pydap_patch_count == 0:
                if not hasattr(pydap.net, "build_session"):
                    raise RuntimeError("pydap internals changed: build_session not found. This integration is pinned to pydap 3.5.10.")
                    
                INCOISClient._original_build_session = pydap.net.build_session
                INCOISClient._original_restore_session = getattr(pydap.net, "restore_session", None)
                
                def incois_build_session(*args, **kwargs):
                    session = INCOISClient._original_build_session(*args, **kwargs)
                    adapter = IncoisHTTPAdapter(self)
                    session.mount("http://incois.gov.in", adapter)
                    session.mount("https://incois.gov.in", adapter)
                    session.mount("http://www.incois.gov.in", adapter)
                    session.mount("https://www.incois.gov.in", adapter)
                    return session

                def incois_restore_session(*args, **kwargs):
                    if INCOISClient._original_restore_session is None:
                        raise NotImplementedError()
                    session = INCOISClient._original_restore_session(*args, **kwargs)
                    adapter = IncoisHTTPAdapter(self)
                    session.mount("http://incois.gov.in", adapter)
                    session.mount("https://incois.gov.in", adapter)
                    session.mount("http://www.incois.gov.in", adapter)
                    session.mount("https://www.incois.gov.in", adapter)
                    return session
                    
                pydap.net.build_session = incois_build_session
                if INCOISClient._original_restore_session is not None:
                    pydap.net.restore_session = incois_restore_session
                    
            self._pydap_patch_count += 1
            
        try:
            yield
        finally:
            with self._pydap_patch_lock:
                self._pydap_patch_count -= 1
                if self._pydap_patch_count == 0:
                    pydap.net.build_session = INCOISClient._original_build_session
                    if INCOISClient._original_restore_session is not None:
                        pydap.net.restore_session = INCOISClient._original_restore_session

# Global Singleton Instance
incois_client = INCOISClient()
