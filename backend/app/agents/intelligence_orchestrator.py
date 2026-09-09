"""Console-only orchestration entry point.

No established endpoint imports this module.  It owns the new intent policy and
the Console-specific agent registry so the legacy planner remains unchanged.
"""
from __future__ import annotations

import asyncio
import dataclasses
import time
from typing import Any, Dict, List

from app.agents.base import AbstractAgent
from app.agents.context import AgentContext, TemporalContext
from app.agents.resilience import ResilienceLayer
from app.agents.result import AgentResult
from app.agents.safety_evidence_agent import SafetyEvidenceAgent
from app.agents.safety_synthesis_agent import SafetySynthesisAgent
from app.agents.console_geospatial_agent import ConsoleGeospatialEvidenceAgent
from app.agents.weather_agent import WeatherIntelligenceAgent
from app.agents.ocean_agent import OceanAnalyticsAgent
from app.agents.risk_agent import RiskAnalysisAgent
from app.agents.reporting_agent import ReportingAgent
from app.agents.research_agent import AcademicResearchAgent
from app.agents.synthesis_agent import ExecutiveSynthesisAgent
from app.models import ChatRequest
from app.agents.intelligence_intent_policy import classify_intent, resolve_console_temporal_context
from app.agents.providers.gee_intelligence_provider import GEEIntelligenceProvider
from app.agents.providers.pfz_cache_provider import PFZCacheProvider
from app.agents.providers.bhashini_translation_provider import BhashiniTranslationProvider
from app.agents.providers.route_intelligence_provider import RouteIntelligenceProvider
from app.agents.providers.research_literature_provider import ResearchLiteratureProvider
from app.api.endpoints.geofence import evaluate_geofence_offline, load_fallback_geojson
from app.services.temporal_analysis import TemporalAnalysisService


class IntelligenceOrchestrator:
    """Runs only the agents deliberately selected for an Intelligence query."""

    def __init__(self) -> None:
        self.resilience = ResilienceLayer()
        self.registry: Dict[str, AbstractAgent] = {
            "safety_evidence": SafetyEvidenceAgent(),
            "geospatial": ConsoleGeospatialEvidenceAgent(),
            "safety_synthesis": SafetySynthesisAgent(),
            # These instances are Console-local.  The legacy PlannerAgent and
            # its shared registry remain unchanged.
            "weather": WeatherIntelligenceAgent(),
            "ocean": OceanAnalyticsAgent(),
            "risk": RiskAnalysisAgent(),
            "reporting": ReportingAgent(),
            "research": AcademicResearchAgent(),
            "synthesis": ExecutiveSynthesisAgent(),
        }

    @staticmethod
    def _is_safety_query(query: str) -> bool:
        terms = ("safe", "safety", "hazard", "venture", "storm", "cyclone", "lightning", "wave", "swell")
        return any(term in query.lower() for term in terms)

    def _select_agents(self, query: str) -> List[str]:
        if self._is_safety_query(query):
            return ["safety_evidence", "geospatial", "safety_synthesis"]
        # Preserve existing Console capabilities while keeping their execution
        # out of the shared PlannerAgent registry.  Intent-specific synthesis
        # is the next step; this route intentionally reports its executed
        # agents rather than presenting an untracked fallback.
        agents = ["weather", "ocean", "geospatial", "risk", "reporting", "synthesis"]
        q = query.lower()
        if any(term in q for term in ("productivity", "decline", "trend", "research")):
            agents.insert(-1, "research")
        return agents

    async def _run_agents(self, context: AgentContext, names: List[str]) -> Dict[str, AgentResult]:
        results: Dict[str, AgentResult] = {}
        remaining = list(names)
        while remaining:
            ready = [name for name in remaining if all(dep in results for dep in self.registry[name].spec.dependencies)]
            if not ready:
                raise RuntimeError("Console agent dependency cycle detected")
            context.prior_results = {name: dataclasses.asdict(result) for name, result in results.items()}
            outputs = await asyncio.gather(
                *(self.resilience.execute_agent(self.registry[name], context) for name in ready),
                return_exceptions=True,
            )
            for name, output in zip(ready, outputs):
                if isinstance(output, Exception):
                    results[name] = AgentResult(agent_name=name, status="failed", data={}, errors=[str(output)])
                else:
                    results[name] = output
            remaining = [name for name in remaining if name not in ready]
        return results

    async def _translate_for_console(self, payload: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Translate only the rendered executive summary, never raw evidence.

        Raw values, sources, timestamps, and safety classifications stay in
        their original structured fields so a translated sentence cannot alter
        the underlying operational evidence.
        """
        summary = payload.get("synthesis", {}).get("executive_summary", "")
        status = await BhashiniTranslationProvider().translate(summary, language)
        if status.get("state") == "LIVE":
            payload["synthesis"]["executive_summary"] = status.pop("text")
        payload["translation"] = status
        return payload

    async def run(self, request: ChatRequest) -> Dict[str, Any]:
        started = time.perf_counter()
        # Intent and temporal routing are deliberately derived from the exact
        # Console request.  The shared LLM resolver is not part of this
        # isolated operational path: it can neither alter intent nor become a
        # prerequisite for source-backed evidence.
        query = request.query
        temporal_data = resolve_console_temporal_context(query)
        context = AgentContext(
            latitude=request.latitude,
            longitude=request.longitude,
            query=query,
            mode="fisheries",
            temporal=TemporalContext(**temporal_data),
        )
        intent = classify_intent(query)
        if intent.name == "route":
            route_result = await RouteIntelligenceProvider().calculate_and_sample(
                request.latitude, request.longitude, request.destination_lat, request.destination_lon
            )
            route = route_result.get("route", {})
            available = route_result.get("state") == "LIVE"
            route_info = route.get("route", {})
            peak = route.get("optimization", {}).get("selected_route_peak_severity")
            samples = route_result.get("nodeSamples", [])
            evidence_states = [
                item.get(section, {}).get("state")
                for item in samples for section in ("weather", "marine")
                if isinstance(item.get(section), dict)
            ]
            usable_samples = sum(state in {"LIVE", "CACHED", "STALE"} for state in evidence_states)
            if available:
                source_sentence = (
                    f"Open-Meteo evidence was available for {usable_samples} of {len(evidence_states)} route-node source samples."
                    if usable_samples else
                    "Open-Meteo route-node evidence is unavailable; the path and BSI peak are not a weather-certified departure recommendation."
                )
                summary = (f"Read-only route analysis found a {route_info.get('distance_km')} km route taking about {route_info.get('duration_hours')} hours. "
                           f"The route engine's predicted peak Boat Safety Index is {peak}/100. {source_sentence} "
                           "Official IMD warning verification is unavailable, so this route is not certified for departure.")
            else:
                summary = route_result.get("reason", "Route evidence is unavailable.")
            payload = {
                "request_id": request.request_id, "state": "live" if available else "error", "intent": "route",
                "assessment": "CAUTION" if available else "ROUTE_UNAVAILABLE", "certification": "PARTIAL",
                "synthesis": {"executive_summary": summary, "identified_hazards": [],
                              "operational_directives": [{"text": "Set a destination and review each sampled node before departure." if available else "Set a destination on the map, then request the route again."}]},
                "evidenceMet": int(available) * 4, "evidenceRequired": 5,
                "sources": ["route_engine", "open_meteo_weather", "open_meteo_marine", "orca_bsi_engine", "imd"], "ragFootnotes": [], "followups": [],
                "mapData": {"activeRoute": route if available else None,
                            "destinationPoint": ({"lat": request.destination_lat, "lon": request.destination_lon} if request.destination_lat is not None and request.destination_lon is not None else None),
                            "routeNodeSamples": route_result.get("nodeSamples", []),
                            "disabledLayers": [{"id": "imd-warning", "title": "Official IMD warnings", "status": "UNAVAILABLE", "unavailableReason": "IMD access and IP whitelisting are pending."}]},
                "execution": {"orchestrationStatus": "success" if available else "incomplete", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                              "agents": {"route_engine": route_result.get("state"), "route_weather_sampling": ("success" if usable_samples else "UNAVAILABLE") if available else "skipped"},
                              "sourceStatus": [{key: value for key, value in route_result.items() if key in {"source", "state", "fetchedAt", "reason"}},
                                               {"source": "imd", "state": "UNAVAILABLE", "reason": "IMD access and IP whitelisting are pending."}],
                              "requiredEvidence": list(intent.required_evidence), "language": request.language},
            }
            return await self._translate_for_console(payload, request.language)
        if intent.name == "ocean_productivity":
            gee = GEEIntelligenceProvider()
            observation = gee.current_ocean_observation(request.latitude, request.longitude)
            layers = gee.current_layers()
            available = observation.get("state") in {"LIVE", "CACHED", "STALE"}
            if available:
                facts = []
                if observation.get("sstC") is not None:
                    facts.append(f"SST {float(observation['sstC']):.1f}°C")
                if observation.get("chlorophyllMgM3") is not None:
                    facts.append(f"chlorophyll {float(observation['chlorophyllMgM3']):.2f} mg/m³")
                summary = (
                    f"Authenticated GEE satellite observation at the selected location reports {', '.join(facts) if facts else 'no usable point values'}. "
                    "The SST and chlorophyll layers show observed ocean conditions, not verified PFZs; use the PFZ query for cache-verified fishing-zone coordinates."
                )
            else:
                summary = (
                    "Regional SST/chlorophyll analysis is unavailable because authenticated Google Earth Engine imagery could not be read. "
                    "No PFZ or favourable-region claim has been substituted for the missing satellite evidence."
                )
            payload = {
                "request_id": request.request_id, "state": "live" if available else "error", "intent": "ocean_productivity",
                "assessment": "OCEAN_OBSERVATION_AVAILABLE" if available else "OCEAN_DATA_UNAVAILABLE", "certification": "PARTIAL",
                "synthesis": {"executive_summary": summary, "identified_hazards": [],
                              "operational_directives": [{"text": "Use this satellite context with a verified PFZ, local restrictions, and a separate safety assessment before departure."}]},
                "evidenceMet": int(available), "evidenceRequired": 2, "sources": ["gee"], "ragFootnotes": [], "followups": [],
                "mapData": {"overlayLayers": layers.get("layers", []), "pfzPoints": [], "geofences": load_fallback_geojson()},
                "execution": {"orchestrationStatus": "success" if available else "incomplete", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                              "agents": {"gee_intelligence": observation.get("state")},
                              "sourceStatus": [{key: value for key, value in item.items() if key in {"source", "state", "fetchedAt", "cacheAgeSeconds", "reason"}} for item in (observation, layers)],
                              "requiredEvidence": list(intent.required_evidence), "language": request.language},
            }
            return await self._translate_for_console(payload, request.language)
        if intent.name == "research":
            history = GEEIntelligenceProvider().historical_annual(request.latitude, request.longitude)
            literature = await ResearchLiteratureProvider().search(query)
            rows = history.get("series", [])
            analysis = history.get("analysis", {})
            temporal = TemporalAnalysisService()
            sst_temporal = temporal.calculate_trend(
                [f"{row['year']}-01-01" for row in rows if row.get("sstC") is not None],
                [row["sstC"] for row in rows if row.get("sstC") is not None],
            )
            chlorophyll_temporal = temporal.calculate_trend(
                [f"{row['year']}-01-01" for row in rows if row.get("chlorophyllMgM3") is not None],
                [row["chlorophyllMgM3"] for row in rows if row.get("chlorophyllMgM3") is not None],
            )
            sst_trend = analysis.get("sstTrendCPerYear")
            chlorophyll_trend = analysis.get("chlorophyllTrendMgM3PerYear")
            correlation = analysis.get("sstChlorophyllCorrelation")
            findings = []
            if sst_trend is not None:
                findings.append(f"SST trend {sst_trend:+.3f}°C/year")
            if chlorophyll_trend is not None:
                findings.append(f"chlorophyll trend {chlorophyll_trend:+.3f} mg/m³/year")
            if correlation is not None:
                findings.append(f"SST–chlorophyll correlation r={correlation:+.2f} across {analysis.get('pairedObservations', 0)} paired annual observations")
            papers = literature.get("papers", [])
            provider_states = literature.get("providerStates", {})
            literature_available = literature.get("state") in {"LIVE", "CACHED", "STALE"}
            research_available = bool(rows) or literature_available
            literature_sentence = (
                f" Literature search returned {len(papers)} supporting scholarly work{'s' if len(papers) != 1 else ''} from "
                f"{', '.join(source for source, state in provider_states.items() if state in {'LIVE', 'CACHED', 'STALE'}) or 'available providers'}.") if papers else (
                " OpenAlex, Crossref, and Europe PMC literature evidence is unavailable for this request.")
            payload = {"request_id": request.request_id, "state": "live" if research_available else "error", "intent": "research", "assessment": "TREND_AVAILABLE" if rows else ("LITERATURE_AVAILABLE" if literature_available else "RESEARCH_UNAVAILABLE"), "certification": "PARTIAL",
                       "synthesis": {"executive_summary": (f"Authenticated GEE historical evidence contains {len(rows)} annual observations: {'; '.join(findings) if findings else 'insufficient complete values for a trend estimate'}. Correlation does not establish causation.{literature_sentence}" if rows else f"Historical GEE evidence is unavailable for this location.{literature_sentence}"), "identified_hazards": [], "operational_directives": [{"text": "Use cited papers as supporting context; do not infer causation from SST/chlorophyll correlation alone."}]},
                       "evidenceMet": int(bool(rows)) + int(literature_available), "evidenceRequired": 2, "sources": ["gee", "openalex", "crossref", "europe_pmc"], "ragFootnotes": papers, "followups": [],
                       "mapData": {"historicalSeries": rows, "historicalAnalysis": analysis,
                                   "temporalAnalysis": {"sst": sst_temporal, "chlorophyll": chlorophyll_temporal},
                                   "literaturePapers": papers, "overlayLayers": GEEIntelligenceProvider().current_layers().get("layers", [])},
                       "execution": {"orchestrationStatus": "success", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2), "agents": {"gee_intelligence": history.get("state"), "temporal_analysis": "success" if rows else "skipped", **{f"research_{source}": state for source, state in provider_states.items()}}, "sourceStatus": [{key: value for key, value in item.items() if key in {"source", "state", "fetchedAt", "cacheAgeSeconds", "reason"}} for item in [history, *literature.get("providers", [])]], "requiredEvidence": list(intent.required_evidence), "language": request.language}}
            return await self._translate_for_console(payload, request.language)
        if intent.name == "pfz":
            pfz = PFZCacheProvider().nearest(request.latitude, request.longitude)
            gee = GEEIntelligenceProvider()
            observation, layers = gee.current_ocean_observation(request.latitude, request.longitude), gee.current_layers()
            geo = evaluate_geofence_offline(request.latitude, request.longitude)
            available = pfz.get("state") in {"CACHED", "LIVE"}
            summary = (f"Nearest cached PFZ is {pfz['distanceKm']:.1f} km away at {pfz['point']['lat']:.3f}, {pfz['point']['lon']:.3f}."
                       if available else "No verified fresh PFZ is available from the local cache.")
            payload = {"request_id": request.request_id, "state": "cached" if available else "error", "intent": "pfz",
                       "assessment": "PFZ_AVAILABLE" if available else "PFZ_UNAVAILABLE", "certification": "PARTIAL",
                       "synthesis": {"executive_summary": summary, "identified_hazards": ([{"text": geo.get("message"), "severity": "CAUTION"}] if geo.get("status") != "SAFE_INSIDE_BORDER" and geo.get("message") else []),
                                     "operational_directives": [{"text": "Verify local restrictions and the cache freshness before departure."}]},
                       "evidenceMet": int(available) + int(observation.get("state") == "LIVE"), "evidenceRequired": 3,
                       "sources": ["incois_pfz_cache", "gee", "geofence"], "ragFootnotes": [], "followups": [],
                       "mapData": {"pfzPoints": ([{"lat": pfz["point"]["lat"], "lon": pfz["point"]["lon"], "properties": {"distanceKm": pfz["distanceKm"], "freshness": pfz["state"]}}] if available else []),
                                   "geofences": load_fallback_geojson(), "overlayLayers": layers.get("layers", [])},
                       "execution": {"orchestrationStatus": "success", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                                     "agents": {"pfz_cache": pfz.get("state"), "gee_intelligence": observation.get("state"), "geospatial": "success"},
                                     "sourceStatus": [{key: value for key, value in item.items() if key in {"source", "state", "fetchedAt", "ageHours", "reason"}} for item in (pfz, observation, layers)], "requiredEvidence": list(intent.required_evidence), "language": request.language}}
            return await self._translate_for_console(payload, request.language)
        names = list(intent.agents) if all(name in self.registry for name in intent.agents) else self._select_agents(query)
        results = await self._run_agents(context, names)
        synthesis = results.get("safety_synthesis") or results.get("synthesis")
        if synthesis.status != "success":
            raise RuntimeError("Safety synthesis could not be completed")
        payload = dict(synthesis.data)
        source_status = [
            {
                "source": source,
                "state": "LIVE" if result.status == "success" else "UNAVAILABLE",
                "agent": name,
                "reason": "; ".join(result.errors) or None,
            }
            for name, result in results.items()
            for source in result.sources
        ]
        # Replace generic agent-success labels with the provider's truthful
        # freshness state.  This is Console-only metadata; it does not affect
        # any legacy provider or route contract.
        safety_result = results.get("safety_evidence")
        safety_data = safety_result.data if safety_result else {}
        for provider_data in (safety_data.get("weather", {}), safety_data.get("marine", {}), safety_data.get("officialWarning", {}), safety_data.get("bsiEvidence", {}), safety_data.get("mlEvidence", {})):
            source = provider_data.get("source")
            if not source:
                continue
            detail = {key: value for key, value in provider_data.items()
                      if key in {"source", "state", "fetchedAt", "cacheAgeSeconds", "reason"}}
            detail["agent"] = "safety_evidence"
            source_status = [item for item in source_status if item.get("source") != source]
            source_status.append(detail)
        map_evidence = safety_data.get("mapEvidence", {})
        if map_evidence.get("source"):
            source_status.append({key: value for key, value in map_evidence.items()
                                  if key in {"source", "state", "fetchedAt", "reason"}})
        # Synthesis repeats the evidence source names for display purposes;
        # the Console trace should retain one authoritative state per source.
        seen_sources = set()
        source_status = [item for item in source_status
                         if not (item.get("source") in seen_sources or seen_sources.add(item.get("source")))]
        payload.update({
            "request_id": request.request_id,
            "state": "live",
            "execution": {
                "orchestrationStatus": "success",
                "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                "agents": {name: result.status for name, result in results.items()},
                "sourceStatus": source_status,
                "temporalContext": temporal_data,
                "language": request.language,
                "requiredEvidence": list(intent.required_evidence),
            },
            "intent": intent.name,
        })
        return await self._translate_for_console(payload, request.language)
