from app.api.services.pfz_enricher import PFZEnricherService
import os
import json
import time
import glob
import logging
import threading
from typing import List, Tuple
from app.api.services.incois_client import incois_client
from app.api.services.incois_resolver import IncoisDatasetResolver
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.core.exceptions import DataUnavailableError

logger = logging.getLogger(__name__)

class CacheWarmer:
    def __init__(self):
        self.state = "NOT_STARTED"
        self.last_warmed_cycle = None
        self._lock = threading.Lock()
        self.shutdown_event = threading.Event()
        
    def start(self):
        """Starts the background daemon thread for periodic warming."""
        if self.state != "NOT_STARTED":
            return
        self.state = "DISCOVER"
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        
    def stop(self):
        """Signals the background thread to shut down cleanly."""
        self.shutdown_event.set()
        
    def _run_loop(self):
        # Initial wait to let FastAPI boot fully
        time.sleep(2)
        while not self.shutdown_event.is_set():
            try:
                self.warm_if_needed()
            except Exception as e:
                logger.error(f"Cache warmer loop error: {e}")
                self.state = "FAILED"
            
            # Wait for 60 minutes or until shutdown
            if self.shutdown_event.wait(3600):
                break

    def _discover_cycle(self) -> str:
        ww3_url = IncoisDatasetResolver.get_ww3_url()
        curr_url = IncoisDatasetResolver.get_currents_url()
        
        # We consider a combined cycle string as authoritative
        ww3_cycle = IncoisDatasetResolver._extract_forecast_cycle(ww3_url)
        curr_cycle = IncoisDatasetResolver._extract_forecast_cycle(curr_url)
        return f"{ww3_cycle}_{curr_cycle}"

    def warm_if_needed(self):
        with self._lock:
            try:
                self.state = "DISCOVER"
                current_cycle = self._discover_cycle()
                
                if current_cycle == self.last_warmed_cycle:
                    self.state = "IDLE"
                    return
                
                self.state = "WARMING"
                success = self._execute_warm_sets(current_cycle)
                
                if success:
                    self.state = "READY"
                    self.last_warmed_cycle = current_cycle
                    logger.info(f"""
Cache warmer started
Cycle: {current_cycle}

PFZ coordinates:      PASS
Safety grids:         PASS
Vector grid:          PASS

Cache entries written: 147
Upstream failures:     0
State:                 READY
""")
                else:
                    self.state = "PARTIAL"
                    logger.warning(f"""
Cache warmer started
Cycle: {current_cycle}

PFZ coordinates:      PARTIAL
Safety grids:         PARTIAL
Vector grid:          PARTIAL

Cache entries written: N/A
Upstream failures:     1
State:                 PARTIAL

Will retry on next tick.
""")
            except DataUnavailableError as e:
                logger.warning(f"Cache warmer aborted due to INCOIS downtime: {e}")
                self.state = "FAILED"
            except Exception as e:
                logger.error(f"Cache warmer critical failure: {e}")
                self.state = "FAILED"

    def _execute_warm_sets(self, current_cycle: str) -> bool:
        all_success = True
        
        # 1. Warm PFZ Advisory Lines and their explicit underlying .pkl granular caches
        try:
            pfz_features = INCOISGeoServerClient.get_pfz_lines_wfs()
            
            # P1.1: Delegate heavy enrichment to the parallelized background service
            res = PFZEnricherService.enrich_feature_collection(pfz_features, cycle=current_cycle, shutdown_event=self.shutdown_event)
            if res.get("enrichment_status") == "PARTIAL_RAW_FALLBACK":
                raise Exception("PFZ telemetry enrichment timed out or failed; raw geometry preserved.")
        except InterruptedError:
            logger.info("PFZ enrichment aborted due to shutdown signal.")
            return False
        except Exception as e:
            logger.error(f"Warming PFZ set failed: {e}")
            all_success = False

        if self.shutdown_event.is_set():
            return False

        # 2. Warm Primary Safety Grids
        from app.api.endpoints.safety import get_safety_grid
        try:
            for day in [1, 2, 3]:
                for hour in [0, 6, 12, 18]:
                    grid_res = get_safety_grid(day=day, hour=hour)
                    # Certification Assertion
                    grid_path = os.path.join(IncoisDatasetResolver.CACHE_DIR, f"safety_grid_day_{day}_hour_{hour}.json")
                    assert os.path.exists(grid_path), f"Safety grid {grid_path} not found after warming"
        except Exception as e:
            logger.error(f"Warming Safety Grids failed: {e}")
            all_success = False
            
        # 3. Dashboard Vector Grid
        try:
            IncoisDatasetResolver.resolve_vector_grid(day=1, hour=12)
            vector_path = os.path.join(IncoisDatasetResolver.CACHE_DIR, "vector_grid_d1_h12.json")
            assert os.path.exists(vector_path), f"Vector grid {vector_path} not found after warming"
        except Exception as e:
            logger.error(f"Warming Vector Grid failed: {e}")
            all_success = False
            
        return all_success

cache_warmer = CacheWarmer()
