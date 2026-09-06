import json
import requests
import time

try:
    with open('../cache/safety_grid_day_1_hour_12.json', 'r') as f:
        grid = json.load(f)
    origin_feat = grid['features'][50]
    dest_feat = grid['features'][51]
    origin = {"lat": origin_feat['properties']['center_lat'], "lon": origin_feat['properties']['center_lon']}
    dest = {"lat": dest_feat['properties']['center_lat'], "lon": dest_feat['properties']['center_lon']}
except:
    origin = {"lat": 5.0, "lon": 65.0}
    dest = {"lat": 6.0, "lon": 66.0}

print(f"👨‍💻 HUMAN: Pointing to {origin} to {dest}...")
payload = {
  "origin": origin,
  "destination": dest,
  "vessel_profile": {"length_m": 15.0, "beam_m": 4.0, "cruising_speed_kn": 12.0},
  "departure_time": "2026-08-26T12:00:00Z",
  "optimize_departure": False
}

res = requests.post("http://127.0.0.1:8000/api/routing/safe-route", json=payload)
data = res.json()
print("\n✅ UI RESPONSE (RAW JSON):")
print(json.dumps(data, indent=2)[:1000] + "\n...")

