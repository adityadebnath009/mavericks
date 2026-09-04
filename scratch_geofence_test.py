import requests
import json
try:
    res = requests.get("http://localhost:8000/api/geofence/geojson")
    print(f"Status: {res.status_code}")
    # print(res.text[:200])
except Exception as e:
    print(f"Exception: {e}")
