import asyncio
import json
import os
import time
from typing import Dict, Any, Callable

class PlannerAgent:
    def __init__(self):
        self.mode = os.getenv("ORCA_MODE", "LIVE")
        self.cache_file = "data/offline_cache.json"

    async def _execute_node(self, agent_name: str, task_func: Callable) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if self.mode == "DEMO":
            cached = self._read_from_cache(agent_name)
            cached["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
            cached["execution_mode"] = "DEMO_CACHE"
            return cached

        try:
            result = await asyncio.wait_for(task_func(), timeout=8.0)
            if isinstance(result, dict):
                result["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
                result["execution_mode"] = "LIVE"
            return result
        except Exception as e:
            print(f"[Failsafe Triggered] {agent_name} failed: {e}. Switching to cache.")
            cached = self._read_from_cache(agent_name)
            cached["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
            cached["execution_mode"] = "FALLBACK_CACHE"
            cached["error_context"] = str(e)
            return cached

    def _read_from_cache(self, agent_name: str) -> Dict[str, Any]:
        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)
                # Supports both flat and scenario-keyed offline caches
                if agent_name in cache:
                    return cache[agent_name]
                for scenario in cache.values():
                    if isinstance(scenario, dict) and agent_name in scenario:
                        return scenario[agent_name]
                return {"status": "cached_fallback", "summary": "Calm conditions."}
        except Exception:
            return {"status": "hardcoded_fallback", "summary": "Safe conditions."}

    async def orchestrate_query(self, weather_func: Callable, ocean_func: Callable) -> Dict[str, Any]:
        start_total = time.perf_counter()
        
        # Execute specialist agents in parallel
        weather_res, ocean_res = await asyncio.gather(
            self._execute_node("weather_agent", weather_func),
            self._execute_node("ocean_agent", ocean_func)
        )

        total_latency = round((time.perf_counter() - start_total) * 1000, 2)

        return {
            "orchestration_status": "success",
            "active_mode": self.mode,
            "total_latency_ms": total_latency,
            "weather_payload": weather_res if isinstance(weather_res, dict) else {"error": str(weather_res)},
            "ocean_payload": ocean_res if isinstance(ocean_res, dict) else {"error": str(ocean_res)}
        }