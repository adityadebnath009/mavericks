import pytest
import os
import json
from unittest.mock import patch
from app.api.services.pfz_enricher import PFZEnricherService, ENRICHMENT_CACHE_FILE
from app.api.services.cache_warmer import CacheWarmer

def test_degraded_incois(monkeypatch):
    dummy_ready = {
        "enrichment_status": "READY",
        "features": [{"type": "Feature", "properties": {"dummy": True}}]
    }
    with open(ENRICHMENT_CACHE_FILE, "w") as f:
        json.dump(dummy_ready, f)
    
    def mock_wfs():
        return {
            "features": [{"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[72.82, 18.96], [72.85, 18.99]]}}]
        }
    monkeypatch.setattr("app.api.services.incois_geoserver.INCOISGeoServerClient.get_pfz_lines_wfs", mock_wfs)
    
    def mock_enrich_point(*args, **kwargs):
        raise Exception("Timeout!")
    monkeypatch.setattr(PFZEnricherService, "enrich_point", mock_enrich_point)
    
    warmer = CacheWarmer()
    warmer._execute_warm_sets("2026-08-30")
    
    with open(ENRICHMENT_CACHE_FILE, "r") as f:
        cache_data = json.load(f)
    assert cache_data["enrichment_status"] == "READY"
    assert cache_data["features"][0]["properties"].get("dummy") is True

    # Note: I need to check how warmer._execute_warm_sets manages self.state
    # Actually wait, warmer is not a singleton if I instantiated it here, but let me just check its state
    # Wait, warmer._execute_warm_sets just returns boolean, but warmer._run_loop handles state
    # I can just assert warmer._execute_warm_sets returns False!
    
