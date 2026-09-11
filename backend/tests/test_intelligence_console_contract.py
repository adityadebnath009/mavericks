"""Contract tests for the isolated `/api/chat` Intelligence Console."""
import asyncio
import time
import pytest

from app.agents.intelligence_intent_policy import classify_intent, resolve_console_followup, resolve_console_temporal_context
from app.agents.intelligence_orchestrator import IntelligenceOrchestrator
from app.agents.providers.gee_intelligence_provider import GEEIntelligenceProvider
from app.agents.providers.route_intelligence_provider import RouteIntelligenceProvider
from app.agents.providers.pfz_cache_provider import PFZCacheProvider
from app.agents.providers.intelligence_marine_provider import IntelligenceMarineProvider
from app.agents.providers.safety_map_provider import SafetyMapProvider
from app.agents.providers.bhashini_translation_provider import BhashiniTranslationProvider
from app.agents.providers.research_literature_provider import ResearchLiteratureProvider
from app.agents.providers.openai_explanation_provider import OpenAIExplanationProvider
from app.agents.safety_evidence_agent import SafetyEvidenceAgent
from app.models import ChatRequest


def _request(query, **values):
    return ChatRequest(query=query, latitude=17.431, longitude=84.703, **values)


@pytest.fixture(autouse=True)
def no_network_narrative(monkeypatch):
    """Keep Console contract tests deterministic; live narration is tested separately."""
    async def unavailable(*_args, **_kwargs):
        return {"state": "UNAVAILABLE", "model": "gpt-4o-mini", "latencyMs": 1, "reason": "test fallback"}
    monkeypatch.setattr(OpenAIExplanationProvider, "narrate", unavailable)


def test_required_problem_statement_queries_select_explicit_console_intents():
    expected = {
        "Where is the nearest PFZ?": "pfz",
        "Is it safe to venture tomorrow?": "safety",
        "Show local sea conditions and tide": "conditions",
        "Are there cyclone alerts nearby?": "alerts",
        "Which regions show high chlorophyll concentration and favourable sea surface temperature?": "ocean_productivity",
        "Find the safest route to destination": "route",
        "Why has fish productivity declined?": "research",
        "Avoid hazards and restricted zones": "geofence_hazards",
    }
    for query, intent in expected.items():
        assert classify_intent(query).name == intent


def test_chlorophyll_change_questions_route_to_temporal_analysis_not_safety_or_pfz():
    for query in ("How is chlorophyll changing?", "How is CHL changing?", "How is chlorophyl changing near my location?"):
        assert classify_intent(query).name == "research"
    assert classify_intent("Show high chlorophyll regions").name == "ocean_productivity"
    assert classify_intent("Where is the nearest PFZ?").name == "pfz"
    assert classify_intent("Compare the SST and chlorophyll trends.").name == "research"


def test_conditions_precede_generic_safety_and_research_policy_names_all_executors():
    assert classify_intent("What is the coastal current now?").name == "conditions"
    assert classify_intent("Show wind and swell conditions tomorrow").name == "conditions"
    assert classify_intent("Is it safe in this current?").name == "safety"
    assert classify_intent("Why has productivity declined versus current SST?").name == "research"
    research = classify_intent("Why has fish productivity declined?")
    assert research.name == "research"
    assert research.agents == ("gee_intelligence", "temporal_analysis", "research_openalex")


def test_console_temporal_policy_never_requires_a_shared_llm():
    assert resolve_console_temporal_context("Is it safe tomorrow?")["mode"] == "forecast"
    assert resolve_console_temporal_context("Show a ten year productivity decline")["mode"] == "research"
    assert resolve_console_temporal_context("What are conditions now?")["mode"] == "live"


def test_followup_resolver_uses_prior_intent_without_substring_misclassification():
    prior = {"intent": "safety", "destination": None}
    why = resolve_console_followup("Why?", prior)
    assert why["applied"] is True
    assert why["resolvedIntent"] == "safety"
    assert "fresh evidence" in why["effectiveQuery"]

    timing = resolve_console_followup("What is the safest window?", prior)
    assert timing["resolvedIntent"] == "safety"
    assert "forecast" in timing["effectiveQuery"]
    assert classify_intent("The departure window is narrow").name == "general_marine"
    assert classify_intent("Show wind conditions").name == "conditions"


def test_explicit_research_question_never_reuses_prior_pfz_context():
    prior = {"intent": "pfz", "destination": None}
    resolution = resolve_console_followup("Why has fish productivity declined in Bay of Bengal?", prior)
    assert resolution["applied"] is False
    assert resolution["resolvedIntent"] is None
    assert resolution["effectiveQuery"] == "Why has fish productivity declined in Bay of Bengal?"
    assert classify_intent(resolution["effectiveQuery"]).name == "research"


def test_only_referential_why_question_reuses_prior_context():
    prior = {"intent": "pfz", "destination": None}
    assert resolve_console_followup("Why?", prior)["resolvedIntent"] == "pfz"
    assert resolve_console_followup("Explain that", prior)["resolvedIntent"] == "pfz"
    assert resolve_console_followup("Why is chlorophyll decreasing?", prior)["applied"] is False


def test_route_followup_requires_destination_without_inventing_one():
    prior = {"intent": "safety", "destination": None}
    resolution = resolve_console_followup("Show a safer route", prior)
    assert resolution["resolvedIntent"] == "route"
    assert resolution["missingRequirement"] == "destination"
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Show a safer route", conversation_context=prior)))
    assert payload["assessment"] == "DESTINATION_REQUIRED"
    assert payload["execution"]["contextResolution"]["missingRequirement"] == "destination"


def test_route_followup_uses_context_destination_when_request_has_none(monkeypatch):
    observed = {}

    async def route_result(_, __, ___, destination_lat, destination_lon):
        observed["destination"] = (destination_lat, destination_lon)
        return {"source": "route_engine", "state": "LIVE", "route": {"route": {"distance_km": 31, "duration_hours": 2.0}, "optimization": {"selected_route_peak_severity": 21}, "path": []}, "nodeSamples": []}

    monkeypatch.setattr(RouteIntelligenceProvider, "calculate_and_sample", route_result)
    prior = {"intent": "safety", "destination": {"lat": 17.7, "lon": 84.9}}
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Show a safer route", conversation_context=prior)))
    assert observed["destination"] == (17.7, 84.9)
    assert payload["execution"]["contextResolution"]["applied"] is True


def test_route_followup_accepts_destination_supplied_with_current_request(monkeypatch):
    observed = {}

    async def route_result(_, __, ___, destination_lat, destination_lon):
        observed["destination"] = (destination_lat, destination_lon)
        return {"source": "route_engine", "state": "LIVE", "route": {"route": {"distance_km": 31, "duration_hours": 2.0}, "optimization": {"selected_route_peak_severity": 21}, "path": []}, "nodeSamples": []}

    monkeypatch.setattr(RouteIntelligenceProvider, "calculate_and_sample", route_result)
    prior = {"intent": "pfz", "destination": None}
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Find the safest route to this verified PFZ.", conversation_context=prior, destination_lat=17.7, destination_lon=84.9)))
    assert observed["destination"] == (17.7, 84.9)
    assert payload["assessment"] == "CAUTION"
    assert payload["execution"]["contextResolution"]["missingRequirement"] is None


def test_console_orchestrator_has_no_shared_llm_selector_dependency():
    orchestrator = IntelligenceOrchestrator()
    assert not hasattr(orchestrator, "llm")
    assert "synthesis" not in orchestrator.registry


def test_safety_remains_partial_without_imd_and_exposes_provider_state(monkeypatch):
    async def evidence(*_args):
        return {"weather": {"source": "open_meteo_weather", "state": "LIVE", "fetchedAt": "2026-09-09T00:00:00Z", "windSpeedKmh": 15, "windGustKmh": 22, "visibilityM": 8000, "precipitationProbability": 10, "windDirectionDeg": 90},
                "marine": {"source": "open_meteo_marine", "state": "LIVE", "fetchedAt": "2026-09-09T00:00:00Z", "waveHeightM": 1.0, "wavePeriodS": 6, "swellHeightM": 0.4, "windWaveHeightM": 0.3, "currentSpeedMs": 0.2, "currentDirectionDeg": 180, "seaSurfaceTemperatureC": 29, "seaLevelHeightMslM": 0.1}}
    async def map_evidence(*_args):
        return {"source": "open_meteo_safety_grid", "state": "LIVE", "bsiGrid": {"type": "FeatureCollection", "features": []}, "windVectors": {"type": "FeatureCollection", "features": []}, "currentVectors": {"type": "FeatureCollection", "features": []}}
    monkeypatch.setattr(IntelligenceMarineProvider, "collect_safety_evidence", evidence)
    monkeypatch.setattr(SafetyMapProvider, "around", map_evidence)
    monkeypatch.setattr(SafetyEvidenceAgent, "_ml_risk", staticmethod(lambda *_args: {"ml_risk_class": "LOW", "model_status": "LIVE"}))
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Is it safe to venture tomorrow?")))
    assert payload["certification"] == "PARTIAL"
    assert payload["evidenceMet"] < payload["evidenceRequired"]
    assert payload["assessment"] in {"SAFE", "CAUTION", "UNSAFE", "PARTIAL"}
    assert any(source["source"] == "imd" and source["state"] == "UNAVAILABLE" for source in payload["execution"]["sourceStatus"])
    assert "Official IMD warning verification is unavailable" in payload["synthesis"]["executive_summary"]
    explanation = payload["mapData"]["explainability"]
    assert explanation["version"] == "orca-explainability-v1"
    assert any(driver["label"] == "Deterministic ORCA BSI" for driver in explanation["drivers"])
    assert any(item["label"] == "Official IMD warning" and item["state"] == "UNAVAILABLE" for item in explanation["safeguards"])
    advisory = payload["synthesis"]["fisherman_advisory"]
    assert "headline" in advisory and advisory["reasons"] and advisory["actions"]
    assert all("XGBoost" not in reason["text"] for reason in advisory["reasons"])


def test_pfz_uses_read_only_cache_and_never_creates_candidate(monkeypatch):
    monkeypatch.setattr(PFZCacheProvider, "nearest", lambda *_args: {"source": "incois_pfz_cache", "state": "CACHED", "fetchedAt": "2026-09-09T00:00:00Z", "ageHours": 2, "point": {"lat": 17.5, "lon": 84.5}, "distanceKm": 12.5})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_ocean_observation", lambda *_args: {"source": "gee", "state": "UNAVAILABLE", "reason": "auth absent"})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_layers", lambda *_args: {"source": "gee", "state": "UNAVAILABLE", "layers": []})
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Nearest PFZ")))
    assert payload["assessment"] == "PFZ_AVAILABLE"
    assert payload["mapData"]["pfzPoints"] == [{"lat": 17.5, "lon": 84.5, "properties": {"distanceKm": 12.5, "freshness": "CACHED"}}]
    assert "12.5 km" in payload["synthesis"]["executive_summary"]


def test_route_requires_destination_then_uses_read_only_route_result(monkeypatch):
    no_destination = asyncio.run(IntelligenceOrchestrator().run(_request("Find a safe route")))
    assert no_destination["assessment"] == "DESTINATION_REQUIRED"
    assert no_destination["certification"] == "PARTIAL"

    async def route_result(*_args):
        return {"source": "route_engine", "state": "LIVE", "fetchedAt": "2026-09-09T00:00:00Z", "route": {"route": {"distance_km": 31, "duration_hours": 2.0}, "optimization": {"selected_route_peak_severity": 21}, "path": [{"node_id": "a", "lat": 17.4, "lon": 84.7, "severity_score": 21}]}, "nodeSamples": []}
    monkeypatch.setattr(RouteIntelligenceProvider, "calculate_and_sample", route_result)
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Find a safe route", destination_lat=17.7, destination_lon=84.9)))
    assert payload["assessment"] == "CAUTION"
    assert payload["mapData"]["activeRoute"]["path"][0]["node_id"] == "a"
    assert payload["certification"] == "PARTIAL"
    assert "route-node evidence is unavailable" in payload["synthesis"]["executive_summary"]
    assert payload["execution"]["agents"]["route_weather_sampling"] == "UNAVAILABLE"


def test_alerts_do_not_equate_missing_model_data_with_no_alert(monkeypatch):
    async def evidence(*_args):
        return {
            "weather": {"source": "open_meteo_weather", "state": "UNAVAILABLE", "reason": "network unavailable"},
            "marine": {"source": "open_meteo_marine", "state": "UNAVAILABLE", "reason": "network unavailable"},
        }
    async def map_evidence(*_args):
        return {"source": "open_meteo_safety_grid", "state": "UNAVAILABLE", "reason": "network unavailable"}
    monkeypatch.setattr(IntelligenceMarineProvider, "collect_safety_evidence", evidence)
    monkeypatch.setattr(SafetyMapProvider, "around", map_evidence)
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Are there lightning or cyclone alerts in my area?")))
    summary = payload["synthesis"]["executive_summary"]
    assert payload["intent"] == "alerts"
    assert "modeled hazard evidence is unavailable" in summary
    assert "no configured threshold breach" not in summary


def test_conditions_explain_live_model_values_and_tide_limit(monkeypatch):
    async def evidence(*_args):
        return {
            "weather": {"source": "open_meteo_weather", "state": "LIVE", "windSpeedKmh": 12, "windGustKmh": 18, "visibilityM": 7000, "precipitationProbability": 20},
            "marine": {"source": "open_meteo_marine", "state": "LIVE", "waveHeightM": 1.1, "swellHeightM": 0.5, "windWaveHeightM": 0.3, "currentSpeedMs": 0.4, "seaLevelHeightMslM": 0.2},
        }
    async def map_evidence(*_args):
        return {"source": "open_meteo_safety_grid", "state": "LIVE"}
    monkeypatch.setattr(IntelligenceMarineProvider, "collect_safety_evidence", evidence)
    monkeypatch.setattr(SafetyMapProvider, "around", map_evidence)
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("What are the tide, weather, and sea conditions near my fishing location?")))
    summary = payload["synthesis"]["executive_summary"]
    assert payload["intent"] == "conditions"
    assert "wind 12.0 km/h" in summary
    assert "Tide-gauge data is unavailable" in summary
    assert "operational model evidence is unavailable" not in summary


def test_openai_narrative_replaces_only_rendered_prose(monkeypatch):
    calls = []
    async def live(_self, payload, query):
        calls.append((payload["intent"], query))
        return {"state": "LIVE", "model": "test-model", "latencyMs": 7, "evidenceContract": "VALIDATED_CONSOLE_EVIDENCE_ONLY", "narrative": {
            "plain_summary": "Simple, grounded explanation.", "what_it_means": "Use the verified evidence shown below.",
            "fisherman_advisory": {"headline": "Check before leaving.", "reasons": [{"title": "Verified condition", "text": "The score and source state remain unchanged."}], "actions": ["Review the evidence ledger."]},
            "limitations": ["Official warning verification remains unavailable."], "followups": ["Show the source freshness."],
        }}
    monkeypatch.setattr(OpenAIExplanationProvider, "narrate", live)
    monkeypatch.setattr(PFZCacheProvider, "nearest", lambda *_args: {"source": "incois_pfz_cache", "state": "CACHED", "point": {"lat": 17.5, "lon": 84.5}, "distanceKm": 12.5})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_ocean_observation", lambda *_args: {"source": "gee", "state": "UNAVAILABLE"})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_layers", lambda *_args: {"source": "gee", "state": "UNAVAILABLE", "layers": []})
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Where is the nearest PFZ?")))
    assert calls == [("pfz", "Where is the nearest PFZ?")]
    assert payload["assessment"] == "PFZ_AVAILABLE"
    assert payload["mapData"]["pfzPoints"][0]["lat"] == 17.5
    assert payload["synthesis"]["executive_summary"] == "Simple, grounded explanation."
    assert payload["execution"]["narrativeAi"]["state"] == "LIVE"


def test_openai_failure_keeps_deterministic_content(monkeypatch):
    async def unavailable(*_args, **_kwargs):
        return {"state": "UNAVAILABLE", "model": "test-model", "latencyMs": 1, "reason": "timeout"}
    monkeypatch.setattr(OpenAIExplanationProvider, "narrate", unavailable)
    monkeypatch.setattr(PFZCacheProvider, "nearest", lambda *_args: {"source": "incois_pfz_cache", "state": "CACHED", "point": {"lat": 17.5, "lon": 84.5}, "distanceKm": 12.5})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_ocean_observation", lambda *_args: {"source": "gee", "state": "UNAVAILABLE"})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_layers", lambda *_args: {"source": "gee", "state": "UNAVAILABLE", "layers": []})
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Where is the nearest PFZ?")))
    assert "12.5 km" in payload["synthesis"]["executive_summary"]
    assert payload["execution"]["narrativeAi"]["state"] == "UNAVAILABLE"


def test_satellite_region_query_does_not_substitute_a_pfz(monkeypatch):
    monkeypatch.setattr(GEEIntelligenceProvider, "current_ocean_observation", lambda *_args: {
        "source": "gee", "state": "LIVE", "fetchedAt": "2026-09-09T00:00:00Z", "sstC": 28.7, "chlorophyllMgM3": 0.45,
    })
    monkeypatch.setattr(GEEIntelligenceProvider, "current_layers", lambda *_args: {"source": "gee", "state": "LIVE", "layers": [{"id": "sst"}, {"id": "chlorophyll"}]})
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Which regions show high chlorophyll concentration and favourable sea surface temperature?")))
    assert payload["intent"] == "ocean_productivity"
    assert payload["assessment"] == "OCEAN_OBSERVATION_AVAILABLE"
    assert payload["mapData"]["pfzPoints"] == []
    assert "not verified PFZs" in payload["synthesis"]["executive_summary"]


def test_research_uses_authenticated_series_analysis(monkeypatch):
    rows = [{"year": 2022, "sstC": 28.0, "chlorophyllMgM3": 0.5}, {"year": 2023, "sstC": 29.0, "chlorophyllMgM3": 0.4}]
    monkeypatch.setattr(GEEIntelligenceProvider, "historical_annual", lambda *_args: {"source": "gee", "state": "LIVE", "series": rows, "analysis": GEEIntelligenceProvider.analyse_annual_series(rows)})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_layers", lambda *_args: {"source": "gee", "state": "LIVE", "layers": []})
    async def literature(*_args):
        return {"source": "research_literature", "state": "LIVE", "providerStates": {"openalex": "LIVE", "crossref": "UNAVAILABLE", "europe_pmc": "UNAVAILABLE"}, "providers": [{"source": "openalex", "state": "LIVE"}], "papers": [{"title": "A peer-reviewed fisheries study", "doi": "https://doi.org/example", "landingPageUrl": "https://doi.org/example", "sources": ["openalex"]}]}
    monkeypatch.setattr(ResearchLiteratureProvider, "search", literature)
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Why has fish productivity declined?")))
    assert payload["assessment"] == "TREND_AVAILABLE"
    assert payload["mapData"]["historicalAnalysis"]["sstChlorophyllCorrelation"] == pytest.approx(-1.0)
    assert payload["mapData"]["temporalAnalysis"]["sst"]["trend_per_year"] == pytest.approx(1.0)
    assert payload["mapData"]["literaturePapers"][0]["title"] == "A peer-reviewed fisheries study"
    assert payload["execution"]["agents"]["research_openalex"] == "LIVE"
    assert "Correlation does not establish causation" in payload["synthesis"]["executive_summary"]


def test_literature_aggregation_deduplicates_doi_and_keeps_provenance():
    from app.agents.providers.research_literature_provider import ResearchLiteratureProvider
    responses = [
        {"source": "openalex", "papers": [{"title": "Marine productivity", "doi": "https://doi.org/10.1/example", "landingPageUrl": "https://example.org", "sources": ["openalex"]}]},
        {"source": "crossref", "papers": [{"title": "Marine Productivity", "doi": "https://doi.org/10.1/example", "citationCount": 5, "sources": ["crossref"]}]},
    ]
    papers = ResearchLiteratureProvider._merge(responses, 6)
    assert len(papers) == 1
    assert papers[0]["citationCount"] == 5
    assert papers[0]["sources"] == ["openalex", "crossref"]


def test_literature_aggregation_filters_non_marine_productivity_results():
    responses = [{"source": "crossref", "papers": [
        {"title": "Labour productivity growth has declined", "doi": "https://doi.org/10.1/economics", "sources": ["crossref"]},
        {"title": "Marine fisheries productivity under ocean warming", "doi": "https://doi.org/10.1/marine", "sources": ["crossref"]},
    ]}]
    papers = ResearchLiteratureProvider._merge(responses, 6)
    assert [paper["title"] for paper in papers] == ["Marine fisheries productivity under ocean warming"]
    assert "marine fisheries productivity decline" in ResearchLiteratureProvider._research_query("Why has fish productivity declined near Visakhapatnam?").lower()


def test_research_timeout_keeps_other_provider_results(monkeypatch):
    from app.agents.providers.openalex_research_provider import OpenAlexResearchProvider
    from app.agents.providers.crossref_research_provider import CrossrefResearchProvider
    from app.agents.providers.europe_pmc_research_provider import EuropePMCResearchProvider

    async def slow_openalex(*_args):
        await asyncio.sleep(0.03)
        return {"source": "openalex", "state": "LIVE", "papers": []}
    async def crossref(*_args):
        return {"source": "crossref", "state": "LIVE", "papers": [{"title": "Marine fisheries productivity", "landingPageUrl": "https://example.org/paper"}]}
    async def europe_pmc(*_args):
        return {"source": "europe_pmc", "state": "UNAVAILABLE", "papers": [], "reason": "offline"}
    monkeypatch.setattr(OpenAlexResearchProvider, "search", slow_openalex)
    monkeypatch.setattr(CrossrefResearchProvider, "search", crossref)
    monkeypatch.setattr(EuropePMCResearchProvider, "search", europe_pmc)
    monkeypatch.setattr(ResearchLiteratureProvider, "_provider_timeout_seconds", 0.001)
    response = asyncio.run(ResearchLiteratureProvider().search("fish productivity"))
    assert response["providerStates"] == {"openalex": "UNAVAILABLE", "crossref": "LIVE", "europe_pmc": "UNAVAILABLE"}
    assert response["state"] == "LIVE"
    assert response["papers"][0]["title"] == "Marine fisheries productivity"


def test_research_keeps_clickable_literature_when_gee_is_unavailable(monkeypatch):
    monkeypatch.setattr(GEEIntelligenceProvider, "historical_annual", lambda *_args: {"source": "gee", "state": "UNAVAILABLE", "reason": "GEE offline"})
    monkeypatch.setattr(GEEIntelligenceProvider, "current_layers", lambda *_args: {"source": "gee", "state": "UNAVAILABLE", "layers": []})
    async def literature(*_args):
        return {"source": "research_literature", "state": "LIVE", "providerStates": {"crossref": "LIVE"}, "providers": [{"source": "crossref", "state": "LIVE"}], "papers": [{"title": "Marine evidence", "landingPageUrl": "https://doi.org/example", "sources": ["crossref"]}]}
    monkeypatch.setattr(ResearchLiteratureProvider, "search", literature)
    payload = asyncio.run(IntelligenceOrchestrator().run(_request("Why has fish productivity declined?")))
    assert payload["assessment"] == "LITERATURE_AVAILABLE"
    assert payload["state"] == "live"
    assert payload["ragFootnotes"][0]["landingPageUrl"] == "https://doi.org/example"


def test_console_provider_exposes_live_cached_then_stale_without_promoting_old_evidence():
    provider = IntelligenceMarineProvider()
    IntelligenceMarineProvider._cache.clear()
    calls = 0

    async def success():
        nonlocal calls
        calls += 1
        return {"fetchedAt": "2026-09-09T00:00:00Z", "windSpeedKmh": 12}

    live = asyncio.run(provider._cached("test_console_source", 17.43, 84.70, "one", 60, success))
    cached = asyncio.run(provider._cached("test_console_source", 17.43, 84.70, "one", 60, success))
    assert live["state"] == "LIVE"
    assert cached["state"] == "CACHED"
    assert calls == 1

    key = provider._key("test_console_source", 17.43, 84.70, "one")
    IntelligenceMarineProvider._cache[key] = (time.monotonic() - 61, live)

    async def failure():
        raise RuntimeError("provider offline")

    stale = asyncio.run(provider._cached("test_console_source", 17.43, 84.70, "one", 60, failure))
    assert stale["state"] == "STALE"
    assert "Live refresh failed" in stale["reason"]
    assert stale["windSpeedKmh"] == 12


def test_bhashini_fallback_does_not_fabricate_hindi_or_marathi(monkeypatch):
    monkeypatch.delenv("BHASHINI_INFERENCE_KEY", raising=False)
    monkeypatch.delenv("BHASHINI_NMT_SERVICE_ID", raising=False)
    monkeypatch.delenv("BHASHINI_TRANSLATION_URL", raising=False)
    monkeypatch.delenv("BHASHINI_API_KEY", raising=False)
    result = asyncio.run(BhashiniTranslationProvider().translate("Safety verdict: CAUTION", "hi-IN"))
    assert result["state"] == "UNAVAILABLE"
    assert result["language"] == "hi-IN"
    assert "not configured" in result["reason"].lower()


def test_bhashini_udyat_translation_uses_native_pipeline_compute(monkeypatch):
    monkeypatch.setenv("BHASHINI_INFERENCE_KEY", "test-inference-key")
    monkeypatch.setenv("BHASHINI_NMT_SERVICE_ID", "ai4bharat/indictrans-v2-all-gpu--t4")
    observed = {}

    class Response:
        def raise_for_status(self): pass
        def json(self): return {"pipelineResponse": [{"output": [{"target": "सुरक्षा स्थिति"}]}]}
    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): pass
        async def post(self, url, **kwargs):
            observed["url"], observed["headers"], observed["payload"] = url, kwargs["headers"], kwargs["json"]
            return Response()
    monkeypatch.setattr("app.agents.providers.bhashini_translation_provider.httpx.AsyncClient", lambda **_kwargs: Client())
    result = asyncio.run(BhashiniTranslationProvider().translate("Safety status", "hi-IN"))
    assert result["state"] == "LIVE"
    assert result["text"] == "सुरक्षा स्थिति"
    assert observed["headers"]["Authorization"] == "test-inference-key"
    assert observed["payload"]["pipelineTasks"][0]["config"]["language"] == {"sourceLanguage": "en", "targetLanguage": "hi"}


def test_console_translates_all_rendered_narrative_or_keeps_all_english(monkeypatch):
    async def translated(_, text, language):
        return {"provider": "bhashini", "state": "LIVE", "language": language, "text": f"HI:{text}"}

    monkeypatch.setattr(BhashiniTranslationProvider, "translate", translated)
    payload = {
        "synthesis": {"executive_summary": "Summary", "identified_hazards": [{"text": "Hazard"}], "operational_directives": [{"text": "Directive"}]},
        "followups": ["Why?"], "execution": {},
    }
    result = asyncio.run(IntelligenceOrchestrator()._translate_for_console(payload, "hi-IN", {"applied": False, "effectiveQuery": "x"}))
    assert result["synthesis"]["executive_summary"] == "HI:Summary"
    assert result["synthesis"]["identified_hazards"][0]["text"] == "HI:Hazard"
    assert result["synthesis"]["operational_directives"][0]["text"] == "HI:Directive"
    assert result["followups"] == ["HI:Why?"]
    assert result["translation"]["translatedFields"] == 4


def test_gee_unavailable_contract_returns_disabled_layers(monkeypatch):
    from app.api.services.gee_service import GEEService

    monkeypatch.setattr(GEEService, "initialize", lambda: False)
    result = GEEIntelligenceProvider().current_layers()
    assert result["state"] == "UNAVAILABLE"
    assert result["layers"]
    assert all(layer["status"] == "UNAVAILABLE" and not layer.get("tiles") for layer in result["layers"])
