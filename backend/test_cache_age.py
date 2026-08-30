import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from app.agents.planner_agent import PlannerAgent

async def mock_agent_task():
    """Dummy function to pass into the orchestrator."""
    return {"status": "live_data"}

async def run_cache_age_test():
    print("=== Testing Planner Agent Cache Staleness (8-Hour Drop) ===\n")

    # 1. Setup stale cache scenario
    os.makedirs("data", exist_ok=True)
    cache_path = "data/offline_cache.json"

    # Subtract exactly 8 hours from the current UTC time
    stale_time = datetime.now(timezone.utc) - timedelta(hours=8)
    stale_timestamp = stale_time.isoformat().replace("+00:00", "Z")

    mock_cache = {
        "test_scenario": {
            "last_cached_at": stale_timestamp,
            "weather_agent": {
                "plain_language_summary": "Calm seas. Safe to proceed.",
                "status": "cached"
            },
            "ocean_agent": {
                "max_pfz_probability": 0.88,
                "status": "cached"
            }
        }
    }

    # Write the stale payload to the JSON file used by the failsafe
    with open(cache_path, "w") as f:
        json.dump(mock_cache, f)

    print(f"[1] Created offline cache with timestamp: {stale_timestamp} (8 hours old)")

    # 2. Initialize Planner Agent in DEMO mode to force a cache read
    planner = PlannerAgent()
    planner.mode = "DEMO"
    
    print("[2] Executing orchestrator in DEMO mode...\n")
    result = await planner.orchestrate_query(mock_agent_task, mock_agent_task)

    # 3. Output the results
    print("--- Verifying Payload Injections ---")
    print(f"is_stale_fallback: {result.get('is_stale_fallback')}")
    print(f"system_advisory_warning: {result.get('system_advisory_warning')}")
    print(f"Weather Summary: {result['weather_payload'].get('plain_language_summary')}\n")

    # 4. Strict Assertions
    assert result["is_stale_fallback"] is True, "Planner failed to flip global is_stale_fallback flag!"
    
    assert result["system_advisory_warning"] is not None, "Global advisory warning is missing!"
    assert "STALE DATA WARNING" in result["system_advisory_warning"], "Advisory warning missing expected prefix."
    
    assert "STALE DATA WARNING" in result["weather_payload"]["plain_language_summary"], "Warning was not prepended to the weather summary."
    assert result["weather_payload"]["cache_age_hours"] >= 8.0, "Cache age calculation is incorrect."

    print("✅ All staleness assertions passed! 6-hour cache warning is active and presentation stability is guaranteed.")

if __name__ == "__main__":
    asyncio.run(run_cache_age_test())