"""Deterministic, Console-only mapping from user intent to evidence policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class IntelligenceIntent:
    name: str
    agents: Tuple[str, ...]
    required_evidence: Tuple[str, ...]


_INTENTS = {
    "route": IntelligenceIntent("route", ("safety_evidence", "geospatial", "safety_synthesis"), ("route_path", "wind", "waves", "currents", "geofence")),
    "geofence_hazards": IntelligenceIntent("geofence_hazards", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "waves", "currents", "geofence")),
    "alerts": IntelligenceIntent("alerts", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "gust", "precipitation", "visibility", "waves", "official_warning")),
    "safety": IntelligenceIntent("safety", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "gust", "visibility", "waves", "swell", "currents", "geofence")),
    "research": IntelligenceIntent("research", ("gee_intelligence", "temporal_analysis", "research_openalex"), ("sst_series", "chlorophyll_series")),
    "ocean_productivity": IntelligenceIntent("ocean_productivity", ("gee_intelligence", "geospatial"), ("sst", "chlorophyll", "satellite_imagery")),
    "conditions": IntelligenceIntent("conditions", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "waves", "swell", "currents")),
    "pfz": IntelligenceIntent("pfz", ("gee_intelligence", "geospatial"), ("sst", "chlorophyll", "geofence")),
    "general_marine": IntelligenceIntent("general_marine", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "waves", "currents", "geofence")),
}


def _contains_any(text: str, terms: Tuple[str, ...]) -> bool:
    """Match complete words/phrases only (``window`` is not ``wind``)."""
    return any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for term in terms)


def get_intent(name: str) -> IntelligenceIntent:
    return _INTENTS.get(name, _INTENTS["general_marine"])


def resolve_console_followup(query: str, prior: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve natural references against an optional prior Console turn.

    This is intentionally deterministic and Console-only.  Explicit new
    requests win; short/anaphoric requests may reuse the prior intent.
    """
    result: Dict[str, Any] = {
        "applied": False, "resolvedIntent": None, "effectiveQuery": query,
        "reason": None, "missingRequirement": None,
    }
    if not isinstance(prior, dict):
        return result
    prior_intent = prior.get("intent")
    if prior_intent not in _INTENTS:
        return result
    q = " ".join(query.lower().split())
    if not q:
        return result
    # A clearly new marine task must never be overwritten by prior context.
    explicit_new_task = _contains_any(q, (
        "pfz", "fishing zone", "chlorophyll", "chlorophyl", "chl", "sea surface temperature", "sst",
        "cyclone", "lightning", "alert", "warning", "research", "productivity",
        "avoid", "restricted", "restriction", "geofence", "geofencing", "boundary", "boundaries",
    ))
    route_request = _contains_any(q, ("route", "path", "waypoint", "destination")) or bool(re.search(r"\bsafer\s+route\b", q))
    # Only a short, referential question is an explanation follow-up.  A
    # substantive question may also begin with "why" (for example, a new
    # productivity-research request), and must retain its own intent.
    why_request = bool(re.fullmatch(
        r"(?:why|explain)(?:\s+(?:that|this|it|the\s+previous\s+(?:result|answer|assessment)))?[?!\.]*",
        q,
    ))
    safest_time = bool(re.search(r"\b(safest|best)\s+(time|window)\b", q))
    reference_request = bool(re.search(r"\b(that|this|it|there|same|previous|again|map)\b", q))
    short_request = len(re.findall(r"\w+", q)) <= 12
    if route_request:
        result.update({"applied": True, "resolvedIntent": "route", "effectiveQuery": "Find the safest route using the previous operating context and forecast evidence.", "reason": "route follow-up"})
        if not isinstance(prior.get("destination"), dict):
            result["missingRequirement"] = "destination"
        return result
    if explicit_new_task:
        return result
    if why_request:
        result.update({"applied": True, "resolvedIntent": prior_intent, "effectiveQuery": f"Explain the previous {prior_intent} assessment using fresh evidence at the selected operating location.", "reason": "evidence explanation follow-up"})
        return result
    if safest_time:
        result.update({"applied": True, "resolvedIntent": "safety", "effectiveQuery": "Find the safest forecast departure time at the selected operating location using fresh safety evidence.", "reason": "forecast safety-window follow-up"})
        return result
    if short_request and reference_request and not explicit_new_task:
        result.update({"applied": True, "resolvedIntent": prior_intent, "effectiveQuery": f"Continue the previous {prior_intent} request using fresh evidence at the selected operating location: {query}", "reason": "contextual reference follow-up"})
    return result


def classify_intent(query: str) -> IntelligenceIntent:
    q = query.lower()
    ocean_terms = ("chlorophyll", "chlorophyl", "chl", "sea surface temperature", "sst")
    change_terms = ("change", "changing", "trend", "increase", "increasing", "decrease", "decreasing", "decline", "history", "historical", "compare", "comparison", "correlation")
    if _contains_any(q, ("route", "path", "waypoint", "destination")):
        return get_intent("route")
    # Requests about where a fisher must keep clear need both the current
    # marine conditions and the selected-point EEZ/MPA evidence.  This comes
    # before generic safety/conditions matching so "hazardous fishing zones"
    # cannot silently become a weather-only answer.
    if _contains_any(q, ("avoid", "avoided", "restricted", "restriction", "geofence", "geofencing", "boundary", "boundaries")):
        return get_intent("geofence_hazards")
    if _contains_any(q, ("alert", "warning", "cyclone", "storm", "lightning")):
        return get_intent("alerts")
    # Explicit operational-safety requests take precedence over a condition
    # word in the same sentence (for example, "is it safe in this current?").
    if _contains_any(q, ("safe", "safety", "venture", "hazard", "hazards")):
        return get_intent("safety")
    # Explicit historical/productivity research is not a conditions request
    # merely because it refers to the current SST as a comparison baseline.
    if _contains_any(q, ("productivity", "decline", "trend", "research")) or (_contains_any(q, ocean_terms) and _contains_any(q, change_terms)):
        return get_intent("research")
    # Satellite-ocean exploration is not a PFZ finding.  Keep it separate so
    # the Console never turns a request for imagery or ocean conditions into a
    # claim that a verified fishing zone exists.
    if (_contains_any(q, ocean_terms)
            and _contains_any(q, ("region", "regions", "where", "show", "high", "favourable", "favorable", "map", "layer"))):
        return get_intent("ocean_productivity")
    # A plain request for observed/forecast marine state needs the dedicated
    # conditions briefing rather than a departure verdict.
    if _contains_any(q, ("tide", "conditions", "current", "wind", "wave", "swell", "visibility", "sea state")):
        return get_intent("conditions")
    if _contains_any(q, ("pfz", "favourable sst", "fishing zone")):
        return get_intent("pfz")
    return get_intent("general_marine")


def resolve_console_temporal_context(query: str) -> dict:
    """Small deterministic temporal contract for Console provider calls.

    This deliberately avoids the shared LLM resolver so an unavailable API key
    cannot delay or alter an operational answer.
    """
    q = query.lower()
    now = datetime.now(timezone.utc).isoformat()
    if any(term in q for term in ("last year", "last 5 years", "last 10 years", "decade", "historical", "trend", "decline", "changing", "increase", "decrease")):
        return {"mode": "research", "start_time": None, "end_time": now, "requested_period": "historical"}
    if any(term in q for term in ("tomorrow", "next week", "forecast", "later today")):
        return {"mode": "forecast", "start_time": now, "end_time": None, "requested_period": "forecast"}
    if any(term in q for term in ("yesterday", "last week", "previous")):
        return {"mode": "historical", "start_time": None, "end_time": now, "requested_period": "historical"}
    return {"mode": "live", "start_time": now, "end_time": None, "requested_period": "now"}
