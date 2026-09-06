import time
from typing import Dict, Any

from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentSnapshot
from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult

class RiskAnalysisAgent(AbstractAgent):
    """Planner-facing wrapper around OrcaBsiEngine for deterministic safety logic."""

    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="risk",
            dependencies=["weather", "ocean", "geospatial"],
            mode_support=["fisheries", "routing"]
        )

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        
        # Extract inputs from prior agents
        weather_res = context.prior_results.get("weather", {})
        ocean_res = context.prior_results.get("ocean", {})
        
        # We handle failures from dependent agents if necessary, 
        # but the planner should have skipped us if they failed.
        
        try:
            # We construct a snapshot and vessel profile
            # Fallbacks are arbitrary constants to ensure graceful evaluation
            snapshot = EnvironmentSnapshot(
                wave_height_m=ocean_res.get("data", {}).get("base_wave_height", 1.0),
                wind_speed_kmh=weather_res.get("data", {}).get("max_wind_speed", 10.0),
            )
            
            vessel = VesselProfile(
                length_m=15.0,
                beam_m=4.0,
                cruising_speed_kn=8.0
            )
            
            # Use deterministic BSI engine
            engine = OrcaBsiEngine()
            bsi_report = engine.evaluate(snapshot, vessel)
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return AgentResult(
                agent_name=self.spec.name,
                status="success",
                data=bsi_report,
                latency_ms=round(latency, 2),
                sources=["orca_bsi_engine"]
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=[str(e)]
            )
