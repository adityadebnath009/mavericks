import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.api.services.pfz_enricher import PFZEnricherService, ENRICHMENT_CACHE_FILE
import os

client = TestClient(app)

def test_pfz_lines_never_enriches(monkeypatch):
    if os.path.exists(ENRICHMENT_CACHE_FILE):
        os.remove(ENRICHMENT_CACHE_FILE)
    
    # Mock to raise if called
    def raise_if_called(*args, **kwargs):
        raise RuntimeError("Synchronous enrichment was invoked!")
        
    monkeypatch.setattr(PFZEnricherService, "enrich_feature_collection", raise_if_called)
    
    response = client.get("/api/incois/pfz-lines")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data.get("enrichment_status") == "PARTIAL_RAW_FALLBACK"

