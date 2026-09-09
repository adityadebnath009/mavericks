"""Read-only local-boundary evidence agent for the Intelligence Console."""
from __future__ import annotations

import time

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult


class ConsoleGeospatialEvidenceAgent(AbstractAgent):
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(name="geospatial", dependencies=[], mode_support=["fisheries", "routing", "weather"])

    async def analyze(self, context: AgentContext) -> AgentResult:
        started = time.perf_counter()
        try:
            # This imports static cache helpers only.  It does not call the
            # endpoint, database, routing engine, or any INCOIS integration.
            from app.api.endpoints.geofence import evaluate_geofence_offline, load_fallback_geojson

            status = evaluate_geofence_offline(context.latitude, context.longitude)
            geojson = load_fallback_geojson()
            return AgentResult(
                agent_name=self.spec.name, status="success",
                data={"geofence": status, "geojson": geojson, "geofence_alerts": [status["message"]] if status["status"] != "SAFE_INSIDE_BORDER" else []},
                latency_ms=round((time.perf_counter() - started) * 1000, 2), sources=["local_geofence_cache"],
            )
        except Exception as exc:
            return AgentResult(agent_name=self.spec.name, status="failed", data={}, errors=[str(exc)], sources=["local_geofence_cache"])
