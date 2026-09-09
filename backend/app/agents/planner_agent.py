import time
import asyncio
from typing import Dict, Any, List

from app.agents.base import AbstractAgent
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.agents.resilience import ResilienceLayer

from app.agents.weather_agent import WeatherIntelligenceAgent
from app.agents.ocean_agent import OceanAnalyticsAgent
from app.agents.geospatial_agent import GeospatialReasoningAgent
from app.agents.risk_agent import RiskAnalysisAgent
from app.agents.reporting_agent import ReportingAgent
from app.agents.research_agent import AcademicResearchAgent
from app.agents.synthesis_agent import ExecutiveSynthesisAgent

# Lightweight registry
AGENT_REGISTRY: Dict[str, AbstractAgent] = {
    "weather": WeatherIntelligenceAgent(),
    "ocean": OceanAnalyticsAgent(),
    "geospatial": GeospatialReasoningAgent(),
    "risk": RiskAnalysisAgent(),
    "reporting": ReportingAgent(),
    "research": AcademicResearchAgent(),
    "synthesis": ExecutiveSynthesisAgent(),
}

class PlannerAgent:
    """
    DAG Intent Decomposer & Central Orchestrator.
    Topologically sorts requested agents based on dependencies and executes them
    concurrently layer by layer.
    """
    def __init__(self):
        self.resilience = ResilienceLayer()

    def _build_execution_layers(self, requested_agent_names: List[str]) -> List[List[str]]:
        """
        Kahn-style topological sort. Returns a list of layers, where each layer
        is a list of agent names that can be executed concurrently.
        """
        # Determine effective subgraph
        in_degree = {name: 0 for name in requested_agent_names}
        adj = {name: [] for name in requested_agent_names}
        
        for name in requested_agent_names:
            agent = AGENT_REGISTRY[name]
            for dep in agent.spec.dependencies:
                if dep in requested_agent_names:
                    adj[dep].append(name)
                    in_degree[name] += 1
                
        layers = []
        # Find nodes with 0 in-degree for the first layer
        current_layer = [name for name in requested_agent_names if in_degree[name] == 0]
        
        while current_layer:
            layers.append(current_layer)
            next_layer = []
            for node in current_layer:
                for neighbor in adj[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_layer.append(neighbor)
            current_layer = next_layer
            
        # Check for cycles
        if sum(len(layer) for layer in layers) != len(requested_agent_names):
            raise ValueError("Cycle detected in agent dependencies")
            
        return layers

    async def orchestrate(self, context: AgentContext, agents: List[str] = None) -> Dict[str, Any]:
        start_total = time.perf_counter()
        
        # Determine required agents based on mode if not explicitly provided
        if not agents:
            agents = [
                name for name, agent in AGENT_REGISTRY.items() 
                if context.mode in agent.spec.mode_support
            ]
            
        try:
            execution_layers = self._build_execution_layers(agents)
        except ValueError as e:
            return {"orchestration_status": "error", "error": str(e)}

        results_dict: Dict[str, AgentResult] = {}
        failed_agents = set()

        # Execute layer by layer
        for layer in execution_layers:
            tasks = []
            valid_agents_in_layer = []
            
            for agent_name in layer:
                agent = AGENT_REGISTRY[agent_name]
                
                # Check if any dependencies failed or were skipped
                deps_failed = any(dep in failed_agents for dep in agent.spec.dependencies)
                if deps_failed:
                    results_dict[agent_name] = AgentResult(
                        agent_name=agent_name,
                        status="skipped",
                        data={},
                        errors=[f"Skipped due to upstream failure in dependencies: {agent.spec.dependencies}"]
                    )
                    failed_agents.add(agent_name)
                    continue
                
                valid_agents_in_layer.append(agent)
                # Ensure prior results are injected into context
                import dataclasses
                context.prior_results = {k: dataclasses.asdict(v) if isinstance(v, AgentResult) else v for k, v in results_dict.items()}
                tasks.append(self.resilience.execute_agent(agent, context))

            if tasks:
                layer_results = await asyncio.gather(*tasks, return_exceptions=True)
                for agent, result in zip(valid_agents_in_layer, layer_results):
                    if isinstance(result, Exception):
                        results_dict[agent.spec.name] = AgentResult(
                            agent_name=agent.spec.name,
                            status="failed",
                            data={},
                            errors=[str(result)]
                        )
                        failed_agents.add(agent.spec.name)
                    else:
                        results_dict[agent.spec.name] = result
                        if result.status in ("failed", "unavailable"):
                            failed_agents.add(agent.spec.name)

        total_latency = round((time.perf_counter() - start_total) * 1000, 2)
        
        # Check if any component fell back to stale cache
        is_any_stale = any(r.status == "cached_stale" for r in results_dict.values())
        global_warnings = [w for r in results_dict.values() for w in r.warnings]

        # Ensure compatibility with frontend (Phase 5 compatibility)
        weather_payload = results_dict.get("weather").data if "weather" in results_dict else {}
        ocean_payload = results_dict.get("ocean").data if "ocean" in results_dict else {}
        synthesis_payload = results_dict.get("synthesis").data if "synthesis" in results_dict else {}

        import dataclasses
        return {
            "orchestration_status": "success",
            "active_mode": self.resilience.mode,
            "total_latency_ms": total_latency,
            "is_stale_fallback": is_any_stale,
            "system_advisory_warning": " | ".join(global_warnings) if global_warnings else None,
            "agent_results": {k: dataclasses.asdict(v) for k, v in results_dict.items()},
            "pipeline_result": synthesis_payload,
            # Legacy payloads for router/frontend compatibility
            "weather_payload": weather_payload,
            "ocean_payload": ocean_payload
        }
