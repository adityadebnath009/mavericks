import sys
sys.path.append('backend')
from app.api.services.geofence import GeofenceService
import json

with open('cache/safety_grid_day_1_hour_12.json', 'r') as f:
    grid = json.load(f)

valid_points = []
for feat in grid['features']:
    lat = feat['properties']['center_lat']
    lon = feat['properties']['center_lon']
    # Check if in EEZ (we mock this or check if it throws)
    # Actually, GeofenceService.check_geofence_status requires DB.
    try:
        status = GeofenceService.check_geofence_status(lat, lon)
        if status.get("is_inside_eez"):
            valid_points.append((lat, lon))
            if len(valid_points) >= 2:
                break
    except Exception as e:
        pass

print("Valid points inside EEZ:", valid_points)
