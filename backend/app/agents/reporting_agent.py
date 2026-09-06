import time
from typing import Dict, Any

from app.api.services.reporting import ReportingService
from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult

class ReportingAgent(AbstractAgent):
    """Planner-facing wrapper around ReportingService (Fisheries Safety RAG)."""

    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="reporting",
            dependencies=["risk"],
            mode_support=["fisheries"]
        )

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        
        # Extract risk data from prior_results if available
        risk_result = context.prior_results.get("risk", {})
        cause = risk_result.get("primary_hazard", context.query or "General marine conditions inquiry")
        risk_factors = risk_result.get("risk_factors", {})
        
        try:
            # Assuming ReportingService.compile_report is synchronous
            report_data = ReportingService.compile_report(
                cause=cause,
                risk_factors=risk_factors,
                source_ref="ORCA Swarm Assessment",
                top_k=3
            )
            latency = (time.perf_counter() - start_time) * 1000
            
            return AgentResult(
                agent_name=self.spec.name,
                status="success",
                data=report_data,
                latency_ms=round(latency, 2),
                sources=["marine_safety_corpus"]
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=[str(e)]
            )
