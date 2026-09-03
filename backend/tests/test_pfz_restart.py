import time
import os
import json
from fastapi.testclient import TestClient
from app.main import app
from app.api.services.pfz_enricher import ENRICHMENT_CACHE_FILE

client = TestClient(app)

def test_cache_restart_simulation():
    # 1. Generate valid _pfz_cache.json
    dummy_ready = {
        "enrichment_status": "READY",
        "cache_version": 1,
        "pfz_cycle": "2026-08-30",
        "generated_at": "2026-08-30T12:00:00Z",
        "features": [{"type": "Feature", "properties": {"dummy": "survives_restart"}}]
    }
    with open(ENRICHMENT_CACHE_FILE, "w") as f:
        json.dump(dummy_ready, f)
    
    # 2. Call endpoint
    start_time = time.time()
    response = client.get("/api/incois/pfz-lines")
    duration = time.time() - start_time
    
    # 3. Confirm response is the persistent cache
    assert response.status_code == 200
    data = response.json()
    assert data["enrichment_status"] == "READY"
    assert data["features"][0]["properties"].get("dummy") == "survives_restart"
    
    # 4. Confirm instant response
    assert duration < 1.0, f"Restart response took too long: {duration:.2f}s"
    print(f"\nRestart response latency: {duration:.2f}s")
