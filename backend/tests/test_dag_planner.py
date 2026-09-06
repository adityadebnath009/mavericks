import pytest
import asyncio
from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.agents.planner_agent import PlannerAgent
from app.agents.resilience import ResilienceLayer

# Mock Agents for testing the DAG logic

class MockAgent(AbstractAgent):
    def __init__(self, name: str, deps: list, should_fail: bool = False):
        self._name = name
        self._deps = deps
        self._should_fail = should_fail
        
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(name=self._name, dependencies=self._deps, mode_support=["test"])
        
    async def analyze(self, context: AgentContext) -> AgentResult:
        if self._should_fail:
            return AgentResult(agent_name=self._name, status="failed", data={}, errors=["Intentional failure"])
        return AgentResult(agent_name=self._name, status="success", data={"executed": True})

@pytest.mark.asyncio
async def test_dag_topological_ordering():
    """
    Given: Reporting → Risk → Weather + Ocean
    Assert:
      - Weather and Ocean execute first concurrently
      - Risk executes after both complete
      - Reporting executes after Risk completes
    """
    import app.agents.planner_agent as pa
    
    # Override registry for this test
    pa.AGENT_REGISTRY = {
        "weather": MockAgent("weather", []),
        "ocean": MockAgent("ocean", []),
        "geospatial": MockAgent("geospatial", []),
        "risk": MockAgent("risk", ["weather", "ocean", "geospatial"]),
        "reporting": MockAgent("reporting", ["risk"]),
    }
    
    planner = pa.PlannerAgent()
    context = AgentContext(mode="test")
    
    # We can inspect the _build_execution_layers logic directly
    layers = planner._build_execution_layers(["weather", "ocean", "geospatial", "risk", "reporting"])
    
    # Layer 0 must contain independent agents
    assert set(layers[0]) == {"weather", "ocean", "geospatial"}
    # Layer 1 must contain risk
    assert layers[1] == ["risk"]
    # Layer 2 must contain reporting
    assert layers[2] == ["reporting"]
    
    # Verify execution succeeds
    res = await planner.orchestrate(context, ["weather", "ocean", "geospatial", "risk", "reporting"])
    assert res["orchestration_status"] == "success"
    
@pytest.mark.asyncio
async def test_dag_failure_cascading():
    """
    Given: Ocean fails
    Assert:
      - Risk = skipped/unavailable
      - Reporting = skipped/unavailable
      - Weather = still successful
    """
    import app.agents.planner_agent as pa
    
    # Ocean is mocked to fail
    pa.AGENT_REGISTRY = {
        "weather": MockAgent("weather", []),
        "ocean": MockAgent("ocean", [], should_fail=True),
        "geospatial": MockAgent("geospatial", []),
        "risk": MockAgent("risk", ["weather", "ocean", "geospatial"]),
        "reporting": MockAgent("reporting", ["risk"]),
    }
    
    # To prevent ResilienceLayer from hiding the failure with a cache fallback in DEMO mode,
    # force ResilienceLayer to LIVE and no cache file.
    import os
    os.environ["ORCA_MODE"] = "LIVE"
    
    planner = pa.PlannerAgent()
    planner.resilience.mode = "LIVE"
    planner.resilience.cache_file = "/non/existent/file.json"
    
    context = AgentContext(mode="test")
    res = await planner.orchestrate(context, ["weather", "ocean", "geospatial", "risk", "reporting"])
    
    results = res["agent_results"]
    
    # Weather and geospatial should succeed
    assert results["weather"]["status"] == "success"
    assert results["geospatial"]["status"] == "success"
    
    # Ocean should fail
    assert results["ocean"]["status"] in ("failed", "unavailable")
    
    # Risk and reporting should cascade skip
    assert results["risk"]["status"] == "skipped"
    assert results["reporting"]["status"] == "skipped"
