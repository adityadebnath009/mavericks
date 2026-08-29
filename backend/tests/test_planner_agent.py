import asyncio
import json
import os
import time

# Adjust the import path if your PlannerAgent is located elsewhere
from app.agents.planner_agent import PlannerAgent

async def slow_weather_agent():
    """Simulates an API connection drop by sleeping longer than the 10s limit."""
    print("   [Live] Fetching weather data... (This will intentionally hang)")
    await asyncio.sleep(12) 
    return {"status": "live_weather_data"}

async def fast_ocean_agent():
    """Simulates a fast, successful API response."""
    print("   [Live] Fetching ocean data... (Fast)")
    await asyncio.sleep(1)
    return {"status": "live_ocean_data"}

async def test_planner():
    print("=== Testing Planner Agent Orchestration & Failsafes ===\n")
    
    # 1. Setup the mock local JSON cache
    os.makedirs("data", exist_ok=True)
    mock_cache = {
        "weather_agent": {"status": "cached_weather", "wind": "45 km/h", "source": "offline_json"},
        "ocean_agent": {"status": "cached_ocean", "wave": "2.1m", "source": "offline_json"}
    }
    with open("data/offline_cache.json", "w") as f:
        json.dump(mock_cache, f)
        
    planner = PlannerAgent()

    # --- Scenario 1: LIVE mode with Timeout Overrides ---
    print("[Test 1] LIVE Mode - Triggering 10s Timeout Failsafe")
    planner.mode = "LIVE"
    
    start_time = time.time()
    # This will run concurrently. The ocean agent finishes in 1s, the weather agent hangs.
    result_live = await planner.orchestrate_query(slow_weather_agent, fast_ocean_agent)
    elapsed = time.time() - start_time
    
    print(f" -> Elapsed Time: {elapsed:.2f} seconds")
    print(f" -> Weather Payload (Failed/Fallback): {result_live['weather_payload']}")
    print(f" -> Ocean Payload (Success/Live): {result_live['ocean_payload']}\n")
    
    assert "cached_weather" in str(result_live['weather_payload']), "Weather didn't fall back to cache!"
    assert "live_ocean_data" in str(result_live['ocean_payload']), "Ocean didn't return live data!"

    # --- Scenario 2: Instant DEMO mode ---
    print("[Test 2] DEMO Mode - Instant Offline Cache Read")
    planner.mode = "DEMO"
    
    start_time = time.time()
    # Even with the slow 12-second function passed in, DEMO mode should intercept it instantly.
    result_demo = await planner.orchestrate_query(slow_weather_agent, fast_ocean_agent)
    elapsed = time.time() - start_time
    
    print(f" -> Elapsed Time: {elapsed:.4f} seconds")
    print(f" -> Weather Payload: {result_demo['weather_payload']}")
    print(f" -> Ocean Payload: {result_demo['ocean_payload']}\n")
    
    assert elapsed < 1.0, "DEMO mode should be instant and skip execution!"
    
    print("✅ All failsafe assertions passed! Presentation stability guaranteed.")

if __name__ == "__main__":
    asyncio.run(test_planner())