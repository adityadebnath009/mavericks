with open("backend/app/api/endpoints/geofence.py", "r") as f:
    content = f.read()

bad_str = """    return {"type": "FeatureCollection", "features": []}
    except Exception:
        # Return fallback boundaries GeoJSON dataset if DB connection drops
        return load_fallback_geojson()"""

good_str = """    return {"type": "FeatureCollection", "features": []}"""

content = content.replace(bad_str, good_str)

with open("backend/app/api/endpoints/geofence.py", "w") as f:
    f.write(content)
