import os
import json
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

from app.agents.base import AbstractAgent
from app.agents.context import AgentContext
from app.agents.result import AgentResult

class ResilienceLayer:
    """
    Manages execution modes (LIVE/DEMO), timeouts, and cache fallbacks.
    The planner delegates agent execution to this layer to decouple infrastructure concerns.
    """
    def __init__(self, cache_file: str = "data/offline_cache.json", max_cache_age_hours: float = 6.0):
        self.mode = os.getenv("ORCA_MODE", "LIVE")
        self.cache_file = cache_file
        self.max_cache_age_hours = max_cache_age_hours
        self.timeout = 8.0

    def _get_cache_age(self, cached_block: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        now = datetime.now(timezone.utc)
        
        timestamp_str = cached_block.get("last_cached_at")
        if timestamp_str:
            try:
                cached_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                age_hours = (now - cached_time).total_seconds() / 3600.0
                return round(age_hours, 2), timestamp_str
            except Exception:
                pass

        if os.path.exists(self.cache_file):
            mtime = os.path.getmtime(self.cache_file)
            file_time = datetime.fromtimestamp(mtime, tz=timezone.utc)
            age_hours = (now - file_time).total_seconds() / 3600.0
            return round(age_hours, 2), file_time.isoformat()

        return 999.0, None

    def _read_from_cache(self, agent_name: str) -> AgentResult:
        try:
            with open(self.cache_file, "r") as f:
                cache = json.load(f)

            agent_payload = {}
            parent_metadata = {}

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
                return AgentResult(
                    agent_name=agent_name,
                    status="unavailable",
                    data={},
                    warnings=["Offline data unavailable."]
                )

            age_hours, cached_timestamp = self._get_cache_age(parent_metadata)
            is_stale = age_hours > self.max_cache_age_hours
            
            # Format as AgentResult
            # We assume the cached agent_payload is the .data dict, though historically it might have been different
            warnings = []
            status = "cached_recent"
            if is_stale:
                status = "cached_stale"
                warnings.append(
                    f"STALE DATA WARNING: Offline forecast is {age_hours:.1f} hours old "
                    f"(older than {self.max_cache_age_hours:.0f}h limit)."
                )

            return AgentResult(
                agent_name=agent_name,
                status=status,
                data=agent_payload,
                execution_mode="DEMO" if self.mode == "DEMO" else "FALLBACK",
                warnings=warnings,
                sources=["offline_cache"]
            )
        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                status="unavailable",
                data={},
                errors=[f"Cache read error: {str(e)}"]
            )

    async def execute_agent(self, agent: AbstractAgent, context: AgentContext) -> AgentResult:
        if self.mode == "DEMO":
            return self._read_from_cache(agent.spec.name)

        try:
            result = await asyncio.wait_for(agent.analyze(context), timeout=self.timeout)
            result.execution_mode = "LIVE"
            if result.status == "failed":
                # Fallback if agent analysis internally failed
                cache_result = self._read_from_cache(agent.spec.name)
                if cache_result.status != "unavailable":
                    cache_result.errors = result.errors
                    return cache_result
            return result
        except asyncio.TimeoutError:
            cache_result = self._read_from_cache(agent.spec.name)
            cache_result.errors.append("Live agent execution timed out (8s)")
            return cache_result
        except Exception as e:
            cache_result = self._read_from_cache(agent.spec.name)
            cache_result.errors.append(f"Live agent execution failed: {str(e)}")
            return cache_result
