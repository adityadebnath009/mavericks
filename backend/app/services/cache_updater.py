import asyncio
import json
import os
import tempfile
import numpy as np
from datetime import datetime

from app.agents.marine_data_agent import MarineDataDiscoveryAgent
from app.agents.weather_agent import WeatherIntelligenceAgent
from app.agents.ocean_agent import OceanAnalyticsAgent

# Target landing centers / harbors for offline fallback registry
MONITORED_SCENARIOS = {
    "puri_optimal": {"lat": 19.8135, "lon": 85.8312, "name": "Puri Harbour"},
    "goa_safe": {"lat": 15.4909, "lon": 73.8278, "name": "Panaji, Goa"},
    "paradip_cyclone": {"lat": 20.2644, "lon": 86.6715, "name": "Paradip Port"},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "name": "Visakhapatnam"},
    "kochi": {"lat": 9.9312, "lon": 76.2673, "name": "Kochi Harbour"}
}

discovery_agent = MarineDataDiscoveryAgent()
weather_agent = WeatherIntelligenceAgent()
ocean_agent = OceanAnalyticsAgent()

async def refresh_single_scenario(lat: float, lon: float) -> dict:
    """Fetches and processes live intelligence for a single coastal coordinate."""
    # 1. Fetch meteorological & oceanographic arrays
    met_data = await discovery_agent.fetch_meteorological_data(lat, lon, days=1)
    ocean_data = await discovery_agent.fetch_oceanographic_data(lat, lon, days=1)

    # 2. Run Weather Intelligence analysis
    weather_report = weather_agent.analyze(met_data).model_dump()
    weather_report["execution_mode"] = "ROLLING_CACHE"

    # 3. Run Ocean Analytics & PFZ gradient synthesis
    base_wave = ocean_data.wave_height[0] if ocean_data.wave_height else 0.5
    base_sst = ocean_data.sea_surface_temperature[0] if ocean_data.sea_surface_temperature else 26.0

    chl_grid, sst_grid, wave_grid = ocean_agent.synthesize_spatial_area(base_sst, base_wave, grid_size=10)
    pfz_scores, coincidence, hsi_maps = ocean_agent.score_fishing_grounds(chl_grid, sst_grid, wave_grid, 1.0)

    ocean_payload = {
        "max_pfz_probability": round(float(np.max(pfz_scores)), 2),
        "coincidence_edge_detected": bool(np.max(coincidence) > 0.0),
        "highly_suitable_species": [species for species, grid in hsi_maps.items() if np.max(grid) > 0.8],
        "execution_mode": "ROLLING_CACHE"
    }

    return {
        "weather_agent": weather_report,
        "ocean_agent": ocean_payload,
        "last_cached_at": datetime.utcnow().isoformat() + "Z"
    }

async def update_offline_cache(cache_file_path: str = "data/offline_cache.json"):
    """Refreshes all scenarios and performs an atomic write to prevent read collisions."""
    os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
    
    # Load existing cache to preserve data if any individual fetch fails
    current_cache = {}
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r") as f:
                current_cache = json.load(f)
        except Exception:
            current_cache = {}

    for scenario_key, location in MONITORED_SCENARIOS.items():
        try:
            updated_payload = await refresh_single_scenario(location["lat"], location["lon"])
            current_cache[scenario_key] = updated_payload
            print(f"[Cache Updater] Refreshed {scenario_key} ({location['name']}) successfully.")
        except Exception as e:
            print(f"[Cache Updater] Failed refreshing {scenario_key}: {e}. Retaining existing cache.")

    # Atomic write pattern: write to tmp file first, then atomic rename
    dir_name = os.path.dirname(cache_file_path) or "."
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tmp_file:
        json.dump(current_cache, tmp_file, indent=2, default=str)
        temp_name = tmp_file.name

    os.replace(temp_name, cache_file_path)
    print(f"[Cache Updater] offline_cache.json updated atomically at {datetime.utcnow().strftime('%H:%M:%S')} UTC.")

async def periodic_cache_refresh_worker(interval_hours: int = 5, cache_file_path: str = "data/offline_cache.json"):
    """Long-running background loop executing every N hours."""
    interval_seconds = interval_hours * 3600
    while True:
        try:
            print(f"[Cache Worker] Starting rolling cache update (interval: {interval_hours}h)...")
            await update_offline_cache(cache_file_path)
        except Exception as e:
            print(f"[Cache Worker Error] Unhandled exception in updater: {e}")
        
        await asyncio.sleep(interval_seconds)