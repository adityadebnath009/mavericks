"""
Geospatial Reasoning Agent — ORCA Marine Portal (ISRO SIH 2026)

Location: backend/app/agents/geospatial_agent.py

This is the thin orchestration-layer wrapper the Planner is expected
to call — it delegates the actual PostGIS work to
services/geospatial_reasoning.py's GeospatialReasoningService,
matching the split between "agents" (orchestration) and "services"
(computation) already used elsewhere in this codebase.

NOTE: I haven't seen an existing file from app/agents/ yet (e.g.
weather_agent.py), so this wrapper is currently a minimal pass-through.
If the real agent layer does more than delegate — e.g. wraps results in
a shared response schema, adds logging, or handles the async/lambda
dispatch your teammate described earlier — update this to match once
you can share an example.
"""

from app.api.services.geospatial_reasoning import GeospatialReasoningService


class GeospatialReasoningAgent:
    """Planner-facing wrapper around GeospatialReasoningService."""

    @staticmethod
    def analyze(lat: float, lon: float) -> dict:
        return GeospatialReasoningService.analyze(lat, lon)


if __name__ == "__main__":
    import json
    result = GeospatialReasoningAgent.analyze(19.8, 85.85)
    print(json.dumps(result, indent=2))
