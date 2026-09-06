import os

with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

start_marker = '@router.get("/grid")'

idx = content.find(start_marker)
if idx != -1:
    content = content[:idx] + """
_global_grid_cache = {}

@router.get("/grid")
@router.get("/grid/")
def get_safety_grid(
    day: int = Query(1, description="Forecast day to evaluate (1, 2, or 3)"),
    hour: int = Query(12, description="Hour of the day (0, 3, 6, 9, 12, 15, 18, 21)")
):
    import numpy as np
    import time
    from app.api.services.open_meteo_client import open_meteo_client
    from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
    from app.api.services.marine_forecast import MarineForecastService
    import datetime
    
    global _global_grid_cache
    cache_key = f"{day}_{hour}"
    
    if cache_key in _global_grid_cache:
        timestamp, geojson = _global_grid_cache[cache_key]
        if time.time() - timestamp < 3600:
            return geojson

    spacing = 1.0
    half = spacing / 2.0

    target_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=hour, minute=0, second=0, microsecond=0)
    if day > 1:
        target_date += datetime.timedelta(days=day-1)

    coords = []
    for lat_c in np.arange(6.0, 23.0, spacing):
        for lon_c in np.arange(68.0, 93.0, spacing):
            is_land = False
            if 8.5 <= lat_c <= 22.0:
                if lat_c <= 15.0:
                    center_lon = 77.5
                    width = 2.0 + (lat_c - 8.5) * 0.8
                    if abs(lon_c - center_lon) < width:
                        is_land = True
                elif lat_c <= 22.0:
                    if 72.5 <= lon_c <= 86.5:
                        is_land = True
            if 6.0 <= lat_c <= 9.5 and 79.5 <= lon_c <= 82.0:
                is_land = True

            if not is_land:
                coords.append((lat_c, lon_c))

    import concurrent.futures
    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=10.0)
    
    def process_point(c):
        lat, lon = c
        try:
            snap = MarineForecastService.get_environment(lat, lon, target_date)
            res = engine.evaluate(snap, vessel)
            severity = res["severity_score"]
            
            color = "#18C7A0"
            if severity >= 61:
                color = "#FF5C5C"
            elif severity >= 31:
                color = "#FFB547"
            
            return {
                "type": "Feature",
                "properties": {
                    "severity": severity,
                    "color": color,
                    "rating": res.get("rating", "UNKNOWN"),
                    "bsi": res.get("bsi", 0)
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon - half, lat - half],
                        [lon + half, lat - half],
                        [lon + half, lat + half],
                        [lon - half, lat + half],
                        [lon - half, lat - half]
                    ]]
                }
            }
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_point, coords))
        
    features = [r for r in results if r is not None]

    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "source": "orca-bsi-grid",
            "resolution": spacing
        },
        "features": features
    }
    
    _global_grid_cache[cache_key] = (time.time(), geojson)
    return geojson
"""

with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)

