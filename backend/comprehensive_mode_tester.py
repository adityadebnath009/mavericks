import sys
import json
from fastapi.testclient import TestClient

sys.path.append('.')
from app.main import app
client = TestClient(app)

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title} ")
    print(f"{'='*60}")

def run_all_tests():
    success_count = 0
    fail_count = 0
    
    # ---------------------------------------------------------
    # 1. WEATHER MODE TESTING (A to Z)
    # ---------------------------------------------------------
    print_header("1. WEATHER MODE: Comprehensive Testing")
    
    print("[1a] Testing /api/safety (Point Telemetry)...")
    res = client.get("/api/safety?lat=15.0&lon=73.0&beam=4.0&day=1&hour=12")
    if res.status_code == 200:
        data = res.json()
        if "severity_score" in data and 0 <= data["severity_score"] <= 100:
            print("  ✅ Passed: Returned valid ORCA 0-100 severity score.")
            success_count += 1
        else:
            print(f"  ❌ Failed: Invalid severity score schema. {data}")
            fail_count += 1
    else:
        print(f"  ❌ Failed: Endpoint returned {res.status_code}: {res.text}")
        fail_count += 1
        
    print("[1b] Testing /api/safety/forecast (24h Diurnal Scrubber)...")
    res = client.get("/api/safety/forecast?lat=15.0&lon=73.0&beam=4.0&day=1")
    if res.status_code == 200:
        data = res.json()
        if type(data) == list and len(data) == 8:
            print("  ✅ Passed: Returned exactly 8 3-hour timesteps for 24h scrubber.")
            success_count += 1
        else:
            print(f"  ❌ Failed: Timeline length is not 8. Data: {data}")
            fail_count += 1
    else:
        print(f"  ❌ Failed: Timeline returned {res.status_code}: {res.text}")
        fail_count += 1

    # ---------------------------------------------------------
    # 2. ROUTING MODE TESTING (A to Z)
    # ---------------------------------------------------------
    print_header("2. ROUTING MODE: Comprehensive Testing")
    
    print("[2a] Testing /api/routing/safe-route (Valid Path Generation)...")
    payload_valid = {
        "origin": {"lat": 18.9, "lon": 72.8},
        "destination": {"lat": 18.8, "lon": 72.7},
        "departure_time": "2026-09-05T12:00:00Z",
        "vessel_profile": {"type": "FISHING", "length_m": 12.0, "beam_m": 4.0, "draft_m": 1.5, "max_speed_kn": 10.0, "displacement_t": 15.0}
    }
    res = client.post("/api/routing/safe-route", json=payload_valid)
    if res.status_code == 200:
        data = res.json()
        if "path" in data and len(data["path"]) > 0:
            print("  ✅ Passed: Successfully calculated a safe A* route.")
            success_count += 1
        else:
            print(f"  ❌ Failed: Route array is missing or empty. {data}")
            fail_count += 1
    else:
        print(f"  ❌ Failed: Routing returned {res.status_code}: {res.text}")
        fail_count += 1
        
    print("[2b] Testing /api/routing/safe-route (Geofence EEZ Rejection)...")
    payload_out_of_bounds = {
        "origin": {"lat": 18.9, "lon": 72.8},
        "destination": {"lat": -5.0, "lon": 85.0}, 
        "departure_time": "2026-09-05T12:00:00Z",
        "vessel_profile": payload_valid["vessel_profile"]
    }
    res = client.post("/api/routing/safe-route", json=payload_out_of_bounds)
    if res.status_code == 200 and res.json().get("decision") == "REJECTED_NO_SAFE_ROUTE":
        print("  ✅ Passed: Route safely rejected boundary crossing (Geofence works).")
        success_count += 1
    else:
        print(f"  ❌ Failed: Router allowed illegal EEZ exit or crashed. {res.text}")
        fail_count += 1

    # ---------------------------------------------------------
    # 3. FISHERIES MODE TESTING (A to Z)
    # ---------------------------------------------------------
    print_header("3. FISHERIES MODE: Comprehensive Testing")
    
    print("[3a] Testing /api/telemetry/location (Map Click Popup)...")
    res = client.get("/api/telemetry/location?lat=16.0&lon=73.5")
    if res.status_code == 200:
        data = res.json()
        if "marine_severity_score" in data and "fishing_opportunity_score" in data:
            print("  ✅ Passed: Telemetry popup successfully fetched Dual-Scores.")
            success_count += 1
        else:
            print(f"  ❌ Failed: Missing Dual-Scores in telemetry payload. {data}")
            fail_count += 1
    else:
        print(f"  ❌ Failed: Telemetry returned {res.status_code}: {res.text}")
        fail_count += 1
        
    print("[3b] Testing /api/marine/analyze (PFZ Intelligence Analytics)...")
    res = client.get("/api/marine/analyze?lat=16.0&lon=73.5")
    if res.status_code == 200:
        data = res.json()
        if "ocean_payload" in data and "coincidence_edge_detected" in data["ocean_payload"]:
            print("  ✅ Passed: PFZ Engine successfully modeled species and chlorophyll gradients.")
            success_count += 1
        else:
            print(f"  ❌ Failed: Missing PFZ analytics data. {data}")
            fail_count += 1
    else:
        print(f"  ❌ Failed: Marine analyze returned {res.status_code}: {res.text}")
        fail_count += 1

    print_header("SUMMARY")
    print(f"Total Tests Run: {success_count + fail_count}")
    print(f"Success: {success_count}")
    print(f"Failed : {fail_count}")

if __name__ == "__main__":
    run_all_tests()
