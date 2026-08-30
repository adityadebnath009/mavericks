import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Tuple, Optional

class PlannerAgent:
    """
    DAG Intent Decomposer & Central Orchestrator.
    Manages asynchronous parallel execution with LIVE/DEMO toggles and
    validates cache age against a 6-hour staleness threshold.
    """
    def __init__(self):
        self.mode = os.getenv("ORCA_MODE", "LIVE")
        self.cache_file = "data/offline_cache.json"
        self.max_cache_age_hours = 6.0

    def _get_cache_age(self, cached_block: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        """
        Calculates cache age in hours from 'last_cached_at' or the file's modification time.
        """
        now = datetime.now(timezone.utc)
        
        # 1. Prefer ISO timestamp stored in JSON
        timestamp_str = cached_block.get("last_cached_at")
        if timestamp_str:
            try:
                cached_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                age_hours = (now - cached_time).total_seconds() / 3600.0
                return round(age_hours, 2), timestamp_str
            except Exception:
                pass

        # 2. Fallback to file modification time if timestamp_str is missing
        if os.path.exists(self.cache_file):
            mtime = os.path.getmtime(self.cache_file)
            file_time = datetime.fromtimestamp(mtime, tz=timezone.utc)
            age_hours = (now - file_time).total_seconds() / 3600.0
            return round(age_hours, 2), file_time.isoformat()

        return 999.0, None

    def _read_from_cache(self, agent_name: str) -> Dict[str, Any]:
        """
        Retrieves cached JSON payload and inspects data age.
        Injects staleness warnings if data is older than 6 hours.
        """
        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)

            agent_payload = {}
            parent_metadata = {}

            # Search in flat or scenario-keyed caches
            if agent_name in cache:
                agent_payload = cache[agent_name]
                parent_metadata = cache
            else:
                for scenario_key, scenario in cache.items():
                    if isinstance(scenario, dict) and agent_name in scenario:
                        agent_payload = scenario[agent_name]
                        parent_metadata = scenario
                        break

            if not agent_payload:
                return {
                    "status": "cached_fallback",
                    "plain_language_summary": "Offline data unavailable.",
                    "is_stale": True
                }

            # Check cache age
            age_hours, cached_timestamp = self._get_cache_age(parent_metadata)
            is_stale = age_hours > self.max_cache_age_hours

            agent_payload["cache_age_hours"] = age_hours
            agent_payload["cached_at"] = cached_timestamp
            agent_payload["is_stale"] = is_stale

            if is_stale:
                warning_msg = (
                    f"⚠️ STALE DATA WARNING: Offline forecast is {age_hours:.1f} hours old "
                    f"(older than {self.max_cache_age_hours:.0f}h limit). Marine conditions may have changed."
                )
                agent_payload["cache_warning"] = warning_msg

                # Prepend warning to plain language summary for the user interface
                if "plain_language_summary" in agent_payload:
                    agent_payload["plain_language_summary"] = f"{warning_msg} {agent_payload['plain_language_summary']}"

            return agent_payload

        except Exception as e:
            return {
                "status": "hardcoded_fallback",
                "plain_language_summary": "System offline. Please consult local coastal radar.",
                "is_stale": True,
                "error_context": str(e)
            }

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
                result["is_stale"] = False
            return result
        except Exception as e:
            print(f"[Failsafe Triggered] {agent_name} failed: {e}. Switching to cache.")
            cached = self._read_from_cache(agent_name)
            cached["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
            cached["execution_mode"] = "FALLBACK_CACHE"
            cached["error_context"] = str(e)
            return cached

    async def orchestrate_query(self, weather_func: Callable, ocean_func: Callable) -> Dict[str, Any]:
        start_total = time.perf_counter()
        
        weather_res, ocean_res = await asyncio.gather(
            self._execute_node("weather_agent", weather_func),
            self._execute_node("ocean_agent", ocean_func)
        )

        total_latency = round((time.perf_counter() - start_total) * 1000, 2)
        
        # Check if any component fell back to stale cache
        is_any_stale = bool(weather_res.get("is_stale") or ocean_res.get("is_stale"))
        global_warning = weather_res.get("cache_warning") or ocean_res.get("cache_warning")

        return {
            "orchestration_status": "success",
            "active_mode": self.mode,
            "total_latency_ms": total_latency,
            "is_stale_fallback": is_any_stale,
            "system_advisory_warning": global_warning,
            "weather_payload": weather_res,
            "ocean_payload": ocean_res
        }