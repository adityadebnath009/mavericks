with open("backend/app/api/endpoints/geofence.py", "r") as f:
    content = f.read()

start_str = "def get_geofence_geojson(db: Session = db_dependency):"
end_str = "        return load_fallback_geojson()\n"

start_idx = content.find(start_str)
end_idx = content.find(end_str, start_idx) + len(end_str)

new_func = """def get_geofence_geojson(db: Session = db_dependency):
    global _cached_geofence_geojson
    if _cached_geofence_geojson is not None:
        return _cached_geofence_geojson
    
    fallback = load_fallback_geojson()
    if fallback:
        _cached_geofence_geojson = fallback
        return fallback
        
    return {"type": "FeatureCollection", "features": []}
"""

content = content[:start_idx] + new_func + content[end_idx:]

with open("backend/app/api/endpoints/geofence.py", "w") as f:
    f.write(content)
print("Replaced get_geofence_geojson")
