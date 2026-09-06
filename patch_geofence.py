import re

with open("backend/app/api/endpoints/geofence.py", "r") as f:
    content = f.read()

# Replace get_geofence_geojson
old_func = re.search(r'def get_geofence_geojson.*?return {"type": "FeatureCollection", "features": \[]}', content, re.DOTALL)
if not old_func:
    print("Could not find get_geofence_geojson!")
    # Just in case, let's search up to except Exception block
    old_func = re.search(r'def get_geofence_geojson.*?return {"type": "FeatureCollection", "features": features\}', content, re.DOTALL)

if old_func:
    new_func = """def get_geofence_geojson(db: Session = db_dependency):
    \"\"\"
    Fetches simplified geometries of the Indian EEZ boundary and Marine Protected Areas (MPAs)
    in GeoJSON format to render directly on the interactive map.
    NOW FORCED TO ALWAYS USE STATIC FALLBACK TO AVOID DB BLOCKING AND IMPROVE PERFORMANCE.
    \"\"\"
    global _cached_geofence_geojson
    if _cached_geofence_geojson is not None:
        return _cached_geofence_geojson
        
    fallback = load_fallback_geojson()
    if fallback:
        _cached_geofence_geojson = fallback
        return fallback
        
    return {"type": "FeatureCollection", "features": []}"""
    
    # We need to make sure we replace the whole function correctly.
    # Actually it's better to just do a precise string replacement.
