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
from app.models import ChatRequest
from app.agents.intelligence_intent_policy import (
    classify_intent,
    get_intent,
    resolve_console_followup,
    resolve_console_temporal_context,
)
from app.agents.providers.gee_intelligence_provider import GEEIntelligenceProvider
from app.agents.providers.pfz_cache_provider import PFZCacheProvider
from app.agents.providers.bhashini_translation_provider import BhashiniTranslationProvider
from app.agents.providers.openai_explanation_provider import OpenAIExplanationProvider
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

    @staticmethod
    def _followups_for(intent: str, **evidence: Any) -> List[str]:
        """Return next questions that are relevant to the evidence just shown.

        These prompts are intentionally selected from the completed Console
        branch and provider state. They do not assert that missing evidence
        exists and they do not reuse a previous turn's intent.
        """
        if intent == "research":
            prompts = []
            if evidence.get("has_series"):
                prompts.append("Compare the SST and chlorophyll trends.")
            if evidence.get("has_papers"):
                prompts.append("Show the supporting research papers.")
            if not prompts:
                prompts.append("Try the historical trend analysis again when satellite evidence is available.")
            return prompts
        if intent == "pfz":
            prompts = ["Show the PFZ freshness and restriction status."]
            if evidence.get("has_pfz"):
                prompts.append("Is it safe to operate near this PFZ?")
            return prompts
        if intent == "ocean_productivity":
            return ["How is chlorophyll changing over time?", "Where is the nearest verified PFZ?"]
        if intent == "route" and evidence.get("has_route"):
            return ["Explain the highest-risk route segment.", "What is the next lower-risk time window?"]
        return []

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

    async def _translate_for_console(
        self, payload: Dict[str, Any], language: str, context_resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate rendered narrative fields, never structured source evidence.

        Raw values, sources, timestamps, and safety classifications stay in
        their original structured fields so a translated sentence cannot alter
        the underlying operational evidence.
        """
        synthesis = payload.get("synthesis", {})
        text_slots: List[tuple[Dict[str, Any], str]] = []
        if isinstance(synthesis.get("executive_summary"), str) and synthesis["executive_summary"].strip():
            text_slots.append((synthesis, "executive_summary"))
        if isinstance(synthesis.get("plain_language_meaning"), str) and synthesis["plain_language_meaning"].strip():
            text_slots.append((synthesis, "plain_language_meaning"))
        for index, limitation in enumerate(synthesis.get("limitations", []) or []):
            if isinstance(limitation, str) and limitation.strip():
                text_slots.append((synthesis["limitations"], index))
        advisory = synthesis.get("fisherman_advisory", {})
        if isinstance(advisory, dict):
            if isinstance(advisory.get("headline"), str) and advisory["headline"].strip():
                text_slots.append((advisory, "headline"))
            for item in advisory.get("reasons", []) or []:
                if isinstance(item, dict):
                    for field in ("title", "text"):
                        if isinstance(item.get(field), str) and item[field].strip():
                            text_slots.append((item, field))
            for index, action in enumerate(advisory.get("actions", []) or []):
                if isinstance(action, str) and action.strip():
                    text_slots.append((advisory["actions"], index))
        for field in ("identified_hazards", "operational_directives"):
            for item in synthesis.get(field, []) or []:
                if isinstance(item, dict) and isinstance(item.get("text"), str) and item["text"].strip():
                    text_slots.append((item, "text"))
        for index, followup in enumerate(payload.get("followups", []) or []):
            if isinstance(followup, str) and followup.strip():
                text_slots.append((payload["followups"], index))

        if language == "en-IN" or not text_slots:
            status: Dict[str, Any] = await BhashiniTranslationProvider().translate("", language)
        else:
            provider = BhashiniTranslationProvider()
            translated = await asyncio.gather(*(provider.translate(container[key], language) for container, key in text_slots))
            failed = next((item for item in translated if item.get("state") != "LIVE"), None)
            if failed:
                # Keep the whole rendered narrative in English rather than
                # mixing successful fragments with an incomplete translation.
                status = {key: value for key, value in failed.items() if key != "text"}
            else:
                for (container, key), translated_item in zip(text_slots, translated):
                    container[key] = translated_item["text"]
                status = {key: value for key, value in translated[0].items() if key != "text"}
                status["translatedFields"] = len(text_slots)
        payload["translation"] = status
        payload.setdefault("execution", {})["contextResolution"] = {
            key: value for key, value in context_resolution.items() if key != "effectiveQuery"
        }
        return payload

    async def _finalize_console_payload(
        self, payload: Dict[str, Any], request: ChatRequest, context_resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add an optional OpenAI narrative after deterministic evidence is complete.

        The provider may replace only rendered prose.  Assessment, source
        states, spatial facts, citations, and all raw map evidence remain the
        deterministic payload that was assembled before this method runs.
        """
        narrative_result = await OpenAIExplanationProvider().narrate(payload, request.query)
        execution = payload.setdefault("execution", {})
        execution["narrativeAi"] = {
            key: value for key, value in narrative_result.items() if key != "narrative"
        }
        narrative = narrative_result.get("narrative")
        if narrative_result.get("state") == "LIVE" and isinstance(narrative, dict):
            synthesis = payload.setdefault("synthesis", {})
            synthesis["executive_summary"] = narrative["plain_summary"]
            synthesis["fisherman_advisory"] = narrative["fisherman_advisory"]
            synthesis["plain_language_meaning"] = narrative.get("what_it_means", "")
            synthesis["limitations"] = narrative.get("limitations", [])
            if narrative.get("followups"):
                payload["followups"] = narrative["followups"]
        return await self._translate_for_console(payload, request.language, context_resolution)

    @staticmethod
    def _destination_required_payload(request: ChatRequest, resolution: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "request_id": request.request_id,
            "state": "live",
            "intent": "route",
            "assessment": "DESTINATION_REQUIRED",
            "certification": "PARTIAL",
            "synthesis": {
                "executive_summary": "A safer route needs a destination. Set a destination waypoint on the map, then ask again; no route has been invented.",
                "identified_hazards": [],
                "operational_directives": [{"text": "Click the map and choose Set Destination, then request the route again."}],
            },
            "evidenceMet": 0,
            "evidenceRequired": 5,
            "sources": ["route_engine", "open_meteo_weather", "open_meteo_marine", "orca_bsi_engine", "imd"],
            "ragFootnotes": [],
            "followups": [],
            "mapData": {"disabledLayers": [{"id": "imd-warning", "title": "Official IMD warnings", "status": "UNAVAILABLE", "unavailableReason": "IMD access and IP whitelisting are pending."}]},
            "execution": {
                "orchestrationStatus": "needs_input",
                "agents": {"route_engine": "skipped"},
                "sourceStatus": [{"source": "route_engine", "state": "UNAVAILABLE", "reason": "A destination waypoint is required."}],
                "requiredEvidence": list(get_intent("route").required_evidence),
                "language": request.language,
                "contextResolution": {key: value for key, value in resolution.items() if key != "effectiveQuery"},
            },
        }

    async def run(self, request: ChatRequest) -> Dict[str, Any]:
        started = time.perf_counter()
        # Intent and temporal routing are deliberately derived from the exact
        # Console request.  The shared LLM resolver is not part of this
        # isolated operational path: it can neither alter intent nor become a
        # prerequisite for source-backed evidence.
        resolution = resolve_console_followup(request.query, request.conversation_context)
        query = resolution["effectiveQuery"]
        temporal_data = resolve_console_temporal_context(query)
        intent = get_intent(resolution["resolvedIntent"]) if resolution.get("resolvedIntent") else classify_intent(query)
        context_destination = request.conversation_context.get("destination") if isinstance(request.conversation_context, dict) else None
        destination_lat = request.destination_lat if request.destination_lat is not None else (context_destination or {}).get("lat")
        destination_lon = request.destination_lon if request.destination_lon is not None else (context_destination or {}).get("lon")
        # A route action may supply a destination in this request even when
        # the preceding conversational turn had none (for example, routing
        # directly to a just-returned verified PFZ point).
        if resolution.get("missingRequirement") == "destination" and destination_lat is not None and destination_lon is not None:
            resolution = {**resolution, "missingRequirement": None}
        if intent.name == "route" and (destination_lat is None or destination_lon is None):
            return await self._finalize_console_payload(self._destination_required_payload(request, resolution), request, resolution)
        context = AgentContext(
            latitude=request.latitude,
            longitude=request.longitude,
            query=query,
            mode="fisheries",
            temporal=TemporalContext(**temporal_data),
        )
        if intent.name == "route":
            route_result = await RouteIntelligenceProvider().calculate_and_sample(
                request.latitude, request.longitude, destination_lat, destination_lon
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
                "sources": ["route_engine", "open_meteo_weather", "open_meteo_marine", "orca_bsi_engine", "imd"], "ragFootnotes": [], "followups": self._followups_for("route", has_route=available),
                "mapData": {"activeRoute": route if available else None,
                            "destinationPoint": ({"lat": destination_lat, "lon": destination_lon} if destination_lat is not None and destination_lon is not None else None),
                            "routeNodeSamples": route_result.get("nodeSamples", []),
                            "disabledLayers": [{"id": "imd-warning", "title": "Official IMD warnings", "status": "UNAVAILABLE", "unavailableReason": "IMD access and IP whitelisting are pending."}]},
                "execution": {"orchestrationStatus": "success" if available else "incomplete", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                              "agents": {"route_engine": route_result.get("state"), "route_weather_sampling": ("success" if usable_samples else "UNAVAILABLE") if available else "skipped"},
                              "sourceStatus": [{key: value for key, value in route_result.items() if key in {"source", "state", "fetchedAt", "reason"}},
                                               {"source": "imd", "state": "UNAVAILABLE", "reason": "IMD access and IP whitelisting are pending."}],
                              "requiredEvidence": list(intent.required_evidence), "language": request.language},
            }
            return await self._finalize_console_payload(payload, request, resolution)
        if intent.name == "ocean_productivity":
            gee = GEEIntelligenceProvider()
            observation = gee.current_ocean_observation(request.latitude, request.longitude)
            layers = gee.current_layers()
            available = observation.get("state") in {"LIVE", "CACHED", "STALE"}
            chlorophyll_layer = next(
                (item for item in layers.get("layers", []) if item.get("id") in {"gee_chl", "chlorophyll"}), {}
            )
            chlorophyll_usable = (
                observation.get("chlorophyllMgM3") is not None
                and chlorophyll_layer.get("status") not in {"STALE", "UNAVAILABLE"}
            )
            if available:
                facts = []
                if observation.get("sstC") is not None:
                    facts.append(f"SST {float(observation['sstC']):.1f}°C")
                if chlorophyll_usable:
                    facts.append(f"chlorophyll {float(observation['chlorophyllMgM3']):.2f} mg/m³")
                summary = (
                    f"Authenticated GEE satellite observation at the selected location reports {', '.join(facts) if facts else 'no usable point values'}. "
                    + (
                        "The SST and chlorophyll layers show observed ocean conditions, not verified PFZs; use the PFZ query for cache-verified fishing-zone coordinates."
                        if chlorophyll_usable else
                        "Chlorophyll evidence is stale or unavailable, so this response cannot rank favourable regions or claim high-chlorophyll fishing zones. Use the PFZ query only for cache-verified fishing-zone coordinates."
                    )
                )
            else:
                summary = (
                    "Regional SST/chlorophyll analysis is unavailable because authenticated Google Earth Engine imagery could not be read. "
                    "No PFZ or favourable-region claim has been substituted for the missing satellite evidence."
                )
            payload = {
                "request_id": request.request_id, "state": "live" if available else "error", "intent": "ocean_productivity",
                "assessment": ("OCEAN_OBSERVATION_AVAILABLE" if chlorophyll_usable else "OCEAN_OBSERVATION_PARTIAL") if available else "OCEAN_DATA_UNAVAILABLE", "certification": "PARTIAL",
                "synthesis": {"executive_summary": summary, "identified_hazards": [],
                              "operational_directives": [{"text": "Use this satellite context with a verified PFZ, local restrictions, and a separate safety assessment before departure."}]},
                "evidenceMet": int(observation.get("sstC") is not None) + int(chlorophyll_usable), "evidenceRequired": 2, "sources": ["gee"], "ragFootnotes": [], "followups": self._followups_for("ocean_productivity"),
                "mapData": {"overlayLayers": layers.get("layers", []), "pfzPoints": [], "geofences": load_fallback_geojson()},
                "execution": {"orchestrationStatus": "success" if available else "incomplete", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                              "agents": {"gee_intelligence": observation.get("state")},
                              "sourceStatus": [{key: value for key, value in item.items() if key in {"source", "state", "fetchedAt", "cacheAgeSeconds", "reason"}} for item in (observation, layers)],
                              "requiredEvidence": list(intent.required_evidence), "language": request.language},
            }
            return await self._finalize_console_payload(payload, request, resolution)
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
                       "evidenceMet": int(bool(rows)) + int(literature_available), "evidenceRequired": 2, "sources": ["gee", "openalex", "crossref", "europe_pmc"], "ragFootnotes": papers, "followups": self._followups_for("research", has_series=bool(rows), has_papers=bool(papers)),
                       "mapData": {"historicalSeries": rows, "historicalAnalysis": analysis,
                                   "temporalAnalysis": {"sst": sst_temporal, "chlorophyll": chlorophyll_temporal},
                                   "literaturePapers": papers, "overlayLayers": GEEIntelligenceProvider().current_layers().get("layers", [])},
                       "execution": {"orchestrationStatus": "success", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2), "agents": {"gee_intelligence": history.get("state"), "temporal_analysis": "success" if rows else "skipped", **{f"research_{source}": state for source, state in provider_states.items()}}, "sourceStatus": [{key: value for key, value in item.items() if key in {"source", "state", "fetchedAt", "cacheAgeSeconds", "reason"}} for item in [history, *literature.get("providers", [])]], "requiredEvidence": list(intent.required_evidence), "language": request.language}}
            return await self._finalize_console_payload(payload, request, resolution)
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
                       "sources": ["incois_pfz_cache", "gee", "geofence"], "ragFootnotes": [], "followups": self._followups_for("pfz", has_pfz=available),
                       "mapData": {"pfzPoints": ([{"lat": pfz["point"]["lat"], "lon": pfz["point"]["lon"], "properties": {"distanceKm": pfz["distanceKm"], "freshness": pfz["state"]}}] if available else []),
                                   "geofences": load_fallback_geojson(), "overlayLayers": layers.get("layers", [])},
                       "execution": {"orchestrationStatus": "success", "totalLatencyMs": round((time.perf_counter() - started) * 1000, 2),
                                     "agents": {"pfz_cache": pfz.get("state"), "gee_intelligence": observation.get("state"), "geospatial": "success"},
                                     "sourceStatus": [{key: value for key, value in item.items() if key in {"source", "state", "fetchedAt", "ageHours", "reason"}} for item in (pfz, observation, layers)], "requiredEvidence": list(intent.required_evidence), "language": request.language}}
            return await self._finalize_console_payload(payload, request, resolution)
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
        return await self._finalize_console_payload(payload, request, resolution)
