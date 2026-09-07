from typing import Dict, Any
from app.agents.result import AgentResult
from app.agents.context import AgentContext
from app.agents.base import AbstractAgent, AgentSpec
from app.api.services.geospatial_reasoning import evaluate_geofence_offline, compute_safe_route

class GeospatialReasoningAgent(AbstractAgent):
    """
    Geospatial Reasoning Agent - Handles bounds checking against MPAs
    and routing queries.
    """
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="geospatial",
            mode_support=["fisheries", "shipping"],
            dependencies=[]
        )

    async def analyze(self, context: AgentContext) -> AgentResult:
        payload = {}
        
        # Always run geofence check
        geo_result = evaluate_geofence_offline(context.latitude, context.longitude)
        payload.update(geo_result)
        
        # If routing is requested, compute optimal path
        is_routing = "route" in context.query.lower() or "safest" in context.query.lower()
        if is_routing:
            # Assume arbitrary target for demonstration
            target_lat = context.latitude + 1.0
            target_lon = context.longitude + 1.0
            
            route_result = compute_safe_route(
                start_lat=context.latitude, 
                start_lon=context.longitude, 
                target_lat=target_lat, 
                target_lon=target_lon
            )
            payload.update(route_result)
            
        return AgentResult(
            agent_name=self.spec.name,
            status="success",
            data=payload
        )
