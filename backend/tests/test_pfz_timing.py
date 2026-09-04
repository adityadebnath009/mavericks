import time
from fastapi.testclient import TestClient
from app.main import app
from app.api.services.pfz_enricher import ENRICHMENT_CACHE_FILE
import os

client = TestClient(app)

def test_cold_start_timing():
    if os.path.exists(ENRICHMENT_CACHE_FILE):
        os.remove(ENRICHMENT_CACHE_FILE)
    
    start_time = time.time()
    response = client.get("/api/incois/pfz-lines")
    duration = time.time() - start_time
    
    assert response.status_code == 200
    assert duration < 5.0, f"Cold start took too long: {duration:.2f}s"
    print(f"\nCold start latency: {duration:.2f}s")
