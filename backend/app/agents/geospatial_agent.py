import time
from typing import Dict, Any

from app.api.services.geospatial_reasoning import GeospatialReasoningService
from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult

class GeospatialReasoningAgent(AbstractAgent):
    """Planner-facing wrapper around GeospatialReasoningService."""

    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="geospatial",
            dependencies=[],
            mode_support=["fisheries", "research", "routing"]
        )

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        lat = context.latitude
        lon = context.longitude
        
        if lat is None or lon is None:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=["Latitude and longitude are required in context."]
            )
            
        try:
            # We assume GeospatialReasoningService.analyze is synchronous right now, 
            # if it were async we would await it.
            geo_data = GeospatialReasoningService.analyze(lat, lon)
            latency = (time.perf_counter() - start_time) * 1000
            
            return AgentResult(
                agent_name=self.spec.name,
                status="success",
                data=geo_data,
                latency_ms=round(latency, 2),
                sources=["postgis", "marine_protected_areas"]
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=[str(e)]
            )
