import pytest
from datetime import date
from app.agents.context import TemporalContext
from app.agents.llm_orchestrator import LLMOrchestrator
from app.api.services.open_meteo_client import open_meteo_client
from app.services.temporal_analysis import TemporalAnalysisService
from app.services.region_resolver import RegionResolver

@pytest.mark.asyncio
async def test_t1_temporal_context_defaults():
    ctx = TemporalContext()
    assert ctx.mode == "live"
    assert ctx.resolution == "monthly"

@pytest.mark.asyncio
async def test_t2_t3_temporal_resolver():
    orchestrator = LLMOrchestrator()
    # Test deterministic parsing
    res = await orchestrator.resolve_temporal_context("SST between 2018 and 2022")
    assert res["mode"] == "historical"
    assert res["start_date"] == "2018-01-01"
    assert res["end_date"] == "2022-12-31"

@pytest.mark.asyncio
async def test_t11_model_consistency():
    # If historical mode, API client should inject models=era5_ocean
    ctx = TemporalContext(mode="historical", start_date=date(2020,1,1), end_date=date(2021,1,1))
    
    # We monkeypatch the session get to just verify params
    def mock_get(*args, **kwargs):
        class MockResponse:
            def raise_for_status(self): pass
            def json(self): return {"hourly": {}}
        assert "models" in kwargs["params"]
        assert kwargs["params"]["models"] == "era5_ocean"
        assert "forecast_days" not in kwargs["params"]
        return MockResponse()
        
    original_get = open_meteo_client.session.get
    open_meteo_client.session.get = mock_get
    try:
        open_meteo_client.fetch_marine_data(10.0, 80.0, ctx)
    finally:
        open_meteo_client.session.get = original_get

@pytest.mark.asyncio
async def test_t12_region_vs_point():
    resolver = RegionResolver()
    
    # Point
    lats, lons = resolver.resolve("SST near arbitrary location", 10.0, 80.0)
    assert len(lats) == 1
    assert len(lons) == 1
    
    # Region
    lats, lons = resolver.resolve("SST in Bay of Bengal", 10.0, 80.0)
    assert len(lats) > 1
    assert len(lons) > 1

def test_t6_temporal_analysis_trend():
    service = TemporalAnalysisService()
    # Fake monthly data that goes up
    timestamps = [
        "2020-01-01T00:00", "2020-02-01T00:00",
        "2021-01-01T00:00", "2021-02-01T00:00",
        "2022-01-01T00:00"
    ]
    values = [28.0, 28.0, 28.5, 28.5, 29.0]
    trend = service.calculate_trend(timestamps, values)
    assert trend["trend_per_year"] == 0.5
    assert trend["start_mean"] == 28.0
    assert trend["end_mean"] == 29.0
