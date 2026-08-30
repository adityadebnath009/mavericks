import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

# Import your specific agents
from app.agents.marine_data_agent import MarineDataDiscoveryAgent
from app.agents.weather_agent import WeatherIntelligenceAgent
from app.agents.ocean_agent import OceanAnalyticsAgent

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
        
        # Instantiate the specialist crew
        self.data_agent = MarineDataDiscoveryAgent()
        self.weather_agent = WeatherIntelligenceAgent()
        self.ocean_agent = OceanAnalyticsAgent()

    def _get_cache_age(self, cached_block: Dict[str, Any]) -> Tuple[float, Optional[str]]:
        # ... (Keep your existing _get_cache_age logic exactly as is) ...
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

    def _read_from_cache(self, agent_name: str) -> Dict[str, Any]:
        # ... (Keep your existing _read_from_cache logic exactly as is) ...
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
                return {"status": "cached_fallback", "plain_language_summary": "Offline data unavailable.", "is_stale": True}
            age_hours, cached_timestamp = self._get_cache_age(parent_metadata)
            is_stale = age_hours > self.max_cache_age_hours
            agent_payload["cache_age_hours"] = age_hours
            agent_payload["cached_at"] = cached_timestamp
            agent_payload["is_stale"] = is_stale
            if is_stale:
                warning_msg = f"  STALE DATA WARNING: Offline forecast is {age_hours:.1f} hours old (older than {self.max_cache_age_hours:.0f}h limit). Marine conditions may have changed."
                agent_payload["cache_warning"] = warning_msg
                if "plain_language_summary" in agent_payload:
                    agent_payload["plain_language_summary"] = f"{warning_msg} {agent_payload['plain_language_summary']}"
            return agent_payload
        except Exception as e:
            return {"status": "hardcoded_fallback", "plain_language_summary": "System offline.", "is_stale": True, "error_context": str(e)}

    async def _execute_node(self, agent_name: str, task_func) -> Dict[str, Any]:
        # ... (Keep your existing _execute_node logic exactly as is) ...
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

    async def orchestrate_query(self, lat: float, lon: float, days: int = 1, time_factor: float = 0.5) -> Dict[str, Any]:
        """
        Takes concrete coordinates and coordinates the fetch->analyze pipeline for all agents.
        """
        start_total = time.perf_counter()

        # 1. Define the specific pipeline for the Weather Agent
        async def weather_pipeline() -> Dict[str, Any]:
            # Fetch async, process sync
            met_data = await self.data_agent.fetch_meteorological_data(lat, lon, days)
            report = self.weather_agent.analyze(met_data)
            # Pydantic models must be dumped to dicts for JSON serialization
            return report.model_dump() 

        # 2. Define the specific pipeline for the Ocean Agent
        async def ocean_pipeline() -> Dict[str, Any]:
            # Fetch async, process sync
            ocean_data = await self.data_agent.fetch_oceanographic_data(lat, lon, days)
            
            # Use the first hour's data to synthesize the spatial grid
            base_sst = ocean_data.sea_surface_temperature[0] if ocean_data.sea_surface_temperature else 28.0
            base_wave = ocean_data.wave_height[0] if ocean_data.wave_height else 1.0
            
            # Synthesize grid and score
            chl_grid, sst_grid, wave_grid = self.ocean_agent.synthesize_spatial_area(base_sst, base_wave)
            pfz_score, coinc_grid, hsi_maps = self.ocean_agent.score_fishing_grounds(
                chl_grid, sst_grid, wave_grid, time_factor
            )
            
            # Convert NumPy arrays to lists so they can be JSON serialized by the API
            return {
                "average_pfz_score": float(pfz_score.mean()),
                "pfz_grid": pfz_score.tolist(),
                "hsi_maps": {species: grid.tolist() for species, grid in hsi_maps.items()}
            }

        # 3. FAN OUT: Run both pipelines concurrently using your _execute_node failsafe wrapper
        weather_res, ocean_res = await asyncio.gather(
            self._execute_node("weather_agent", weather_pipeline),
            self._execute_node("ocean_agent", ocean_pipeline)
        )

        total_latency = round((time.perf_counter() - start_total) * 1000, 2)
        
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