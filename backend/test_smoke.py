import requests
import json
import time

def run_smoke_test():
    print("=== ORCA Pipeline Smoke Test ===")
    url = "http://127.0.0.1:8000/marine/analyze"
    
    # Test coordinates (Visakhapatnam coast)
    params = {
        "lat": 17.431,
        "lon": 84.703
    }
    
    print(f"\n[1] Pinging endpoint: GET {url}")
    print(f"[2] Parameters: lat={params['lat']}, lon={params['lon']}")
    
    start_time = time.time()
    try:
        # Timeout slightly above the Planner's 10-second failsafe
        response = requests.get(url, params=params, timeout=12)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            payload = response.json()
            print(f"\n✅ Pipeline executed successfully in {elapsed:.2f} seconds!")
            print("\n--- Consolidated Agent Payload ---")
            print(json.dumps(payload, indent=2))
            
            # Verification Assertions
            assert payload.get("orchestration_status") == "success", "Planner failed"
            assert "plain_language_summary" in payload["weather_payload"], "Weather report missing"
            assert "max_pfz_probability" in payload["ocean_payload"], "Ocean analytics missing"
            print("\n✅ All assertions passed. Backend is ready for the frontend team.")
            
        else:
            print(f"\n❌ Server returned error code: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection refused. Is the FastAPI server running?")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    run_smoke_test()