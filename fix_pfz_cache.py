import re

with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

old_func = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    \"\"\"
    Retrieves the WFS GeoJSON features representing Potential Fishing Zones,
    and dynamically augments them with live Open-Meteo current/wave data and ORCA risk scores.
    \"\"\"
    geojson = INCOISGeoServerClient.get_pfz_lines_wfs()"""

new_func = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    \"\"\"
    Retrieves the WFS GeoJSON features representing Potential Fishing Zones,
    and dynamically augments them with live Open-Meteo current/wave data and ORCA risk scores.
    \"\"\"
    import os
    import json
    import time
    
    # 1. Check local augmented cache first
    augmented_cache = "data/cache/pfz_lines_augmented.json"
    os.makedirs(os.path.dirname(augmented_cache), exist_ok=True)
    if os.path.exists(augmented_cache):
        if time.time() - os.path.getmtime(augmented_cache) < 3600: # 1 hour cache
            try:
                with open(augmented_cache, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    geojson = INCOISGeoServerClient.get_pfz_lines_wfs()"""

old_return = """    geojson["features"] = augmented_features
    return geojson"""

new_return = """    geojson["features"] = augmented_features
    
    # Save to augmented cache
    try:
        with open(augmented_cache, "w", encoding="utf-8") as f:
            json.dump(geojson, f)
    except Exception:
        pass
        
    return geojson"""

content = content.replace(old_func, new_func).replace(old_return, new_return)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(content)
