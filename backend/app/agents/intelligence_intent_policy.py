"""Deterministic, Console-only mapping from user intent to evidence policy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple


@dataclass(frozen=True)
class IntelligenceIntent:
    name: str
    agents: Tuple[str, ...]
    required_evidence: Tuple[str, ...]


def classify_intent(query: str) -> IntelligenceIntent:
    q = query.lower()
    if any(term in q for term in ("route", "path", "waypoint", "destination")):
        return IntelligenceIntent("route", ("safety_evidence", "geospatial", "safety_synthesis"), ("route_path", "wind", "waves", "currents", "geofence"))
    if any(term in q for term in ("alert", "warning", "cyclone", "storm", "lightning")):
        return IntelligenceIntent("alerts", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "gust", "precipitation", "visibility", "waves", "official_warning"))
    # Explicit operational-safety requests take precedence over a condition
    # word in the same sentence (for example, "is it safe in this current?").
    if any(term in q for term in ("safe", "safety", "venture", "hazard")):
        return IntelligenceIntent("safety", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "gust", "visibility", "waves", "swell", "currents", "geofence"))
    # Explicit historical/productivity research is not a conditions request
    # merely because it refers to the current SST as a comparison baseline.
    if any(term in q for term in ("productivity", "decline", "trend", "research")):
        return IntelligenceIntent("research", ("gee_intelligence", "temporal_analysis", "research_openalex"), ("sst_series", "chlorophyll_series"))
    # Satellite-ocean exploration is not a PFZ finding.  Keep it separate so
    # the Console never turns a request for imagery or ocean conditions into a
    # claim that a verified fishing zone exists.
    if (any(term in q for term in ("chlorophyll", "sea surface temperature", "sst"))
            and any(term in q for term in ("region", "regions", "where", "show", "high", "favourable", "favorable", "map", "layer"))):
        return IntelligenceIntent("ocean_productivity", ("gee_intelligence", "geospatial"), ("sst", "chlorophyll", "satellite_imagery"))
    # A plain request for observed/forecast marine state needs the dedicated
    # conditions briefing rather than a departure verdict.
    if any(term in q for term in ("tide", "conditions", "current", "wind", "wave", "swell", "visibility", "sea state")):
        return IntelligenceIntent("conditions", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "waves", "swell", "currents"))
    if any(term in q for term in ("pfz", "chlorophyll", "favourable sst", "fishing zone")):
        return IntelligenceIntent("pfz", ("gee_intelligence", "geospatial"), ("sst", "chlorophyll", "geofence"))
    return IntelligenceIntent("general_marine", ("safety_evidence", "geospatial", "safety_synthesis"), ("wind", "waves", "currents", "geofence"))


def resolve_console_temporal_context(query: str) -> dict:
    """Small deterministic temporal contract for Console provider calls.

    This deliberately avoids the shared LLM resolver so an unavailable API key
    cannot delay or alter an operational answer.
    """
    q = query.lower()
    now = datetime.now(timezone.utc).isoformat()
    if any(term in q for term in ("last year", "last 5 years", "last 10 years", "decade", "historical", "trend", "decline")):
        return {"mode": "research", "start_time": None, "end_time": now, "requested_period": "historical"}
    if any(term in q for term in ("tomorrow", "next week", "forecast", "later today")):
        return {"mode": "forecast", "start_time": now, "end_time": None, "requested_period": "forecast"}
    if any(term in q for term in ("yesterday", "last week", "previous")):
        return {"mode": "historical", "start_time": None, "end_time": now, "requested_period": "historical"}
    return {"mode": "live", "start_time": now, "end_time": None, "requested_period": "now"}
