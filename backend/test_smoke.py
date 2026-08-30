import requests
import json
import time

def run_smoke_test():
    print("=== ORCA Pipeline Smoke Test (Upgraded) ===")
    url = "http://127.0.0.1:8000/api/marine/analyze"
    
    # Test coordinates (Visakhapatnam coast)
    params = {
        "lat": 17.431,
        "lon": 84.703
    }
    
    print(f"\n[1] Pinging endpoint: GET {url}")
    print(f"[2] Parameters: lat={params['lat']}, lon={params['lon']}")
    
    start_time = time.time()
    try:
        # Timeout set to 10s to safely clear the Planner Agent's 8s failsafe
        response = requests.get(url, params=params, timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            payload = response.json()
            print(f"\n✅ HTTP Request completed in {elapsed:.2f} seconds")
            print(f"⏱️  Server-side Orchestration Latency: {payload.get('total_latency_ms', 'N/A')} ms")
            print(f"🔧 Active Mode: {payload.get('active_mode', 'N/A')}")
            
            print("\n--- Consolidated Agent Payload ---")
            print(json.dumps(payload, indent=2))
            
            # --- Strict Verification Assertions ---
            assert payload.get("orchestration_status") == "success", "Planner Orchestrator failed"
            
            # Weather Agent Assertions (IMD Upgrades)
            weather = payload.get("weather_payload", {})
            assert "imd_color_code" in weather, "Weather report missing IMD color code"
            assert "weather_safety_score" in weather, "Weather report missing safety score"
            assert "latency_ms" in weather, "Weather Agent missing latency telemetry"
            
            # Ocean Agent Assertions (Spatial Upgrades)
            ocean = payload.get("ocean_payload", {})
            assert "max_pfz_probability" in ocean, "Ocean analytics missing PFZ probability"
            assert "coincidence_edge_detected" in ocean, "Ocean analytics missing spatial coincidence detection"
            assert "latency_ms" in ocean, "Ocean Agent missing latency telemetry"
            
            print("\n✅ All assertions passed! Telemetry, IMD thresholds, and Synthetic Grids are operational.")
            
        else:
            print(f"\n❌ Server returned error code: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection refused. Is the FastAPI server running on port 8000?")
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out. The Planner Agent's failsafe failed to intercept the hanging process.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    run_smoke_test()