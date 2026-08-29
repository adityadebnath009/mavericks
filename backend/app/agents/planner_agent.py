import asyncio
import json
import os
from typing import Dict, Any, Callable

class PlannerAgent:
    """
    DAG Intent Decomposer & Central Orchestrator.
    Manages asynchronous parallel execution with LIVE/DEMO toggles.
    """
    def __init__(self):
        # Pulls the mode set by the PowerShell toggle script
        self.mode = os.getenv("ORCA_MODE", "LIVE")
        self.cache_file = "data/offline_cache.json"

    async def _execute_node(self, agent_name: str, task_func: Callable) -> Dict[str, Any]:
        """Executes an agent task, falling back to cache if in DEMO mode or on timeout."""
        if self.mode == "DEMO":
            return self._read_from_cache(agent_name)

        try:
            # Attempt live execution for the specialist agent
            return await asyncio.wait_for(task_func(), timeout=10.0)
        except Exception as e:
            print(f"⚠️ [Failsafe Triggered] {agent_name} failed: {e}. Switching to local fallback.")
            return self._read_from_cache(agent_name)

    def _read_from_cache(self, agent_name: str) -> Dict[str, Any]:
        """Retrieves cached JSON payload to ensure zero-crash presentations."""
        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)
                return cache.get(agent_name, {"status": "No cache available"})
        except FileNotFoundError:
            return {"error": "Cache file missing"}

    async def orchestrate_query(self, weather_func: Callable, ocean_func: Callable) -> Dict[str, Any]:
        """
        Executes the DAG Intent Decomposer.
        Runs Weather and Ocean Analytics concurrently.
        """
        # Fan-out: Execute parallel nodes
        results = await asyncio.gather(
            self._execute_node("weather_agent", weather_func),
            self._execute_node("ocean_agent", ocean_func),
            return_exceptions=True
        )

        return {
            "orchestration_status": "success",
            "active_mode": self.mode,
            "weather_payload": results[0],
            "ocean_payload": results[1]
        }