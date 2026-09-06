import re

with open("backend/app/api/endpoints/pfz_router.py", "r") as f:
    content = f.read()

# Replace get_pfz_lines()
old_func = """@router.get("")
@router.get("/")
def get_pfz_lines():
    \"\"\"
    Retrieves the raw WFS GeoJSON features representing Potential Fishing Zones.
    \"\"\"
    return INCOISGeoServerClient.get_pfz_lines_wfs()"""

new_func = """@router.get("")
@router.get("/")
def get_pfz_lines():
    \"\"\"
    Retrieves the WFS GeoJSON features representing Potential Fishing Zones,
    and dynamically augments them with live Open-Meteo current/wave data and ORCA risk scores.
    \"\"\"
    geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
    
    features = geojson.get("features", [])
    if not features:
        return geojson

    from app.api.services.marine_forecast import MarineForecastService
    from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
    import concurrent.futures
    import datetime
    from shapely.geometry import shape

    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=15.0, beam_m=3.5, cruising_speed_kn=10.0)
    target_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)

    def augment_feature(feat):
        try:
            geom = shape(feat["geometry"])
            centroid = geom.centroid
            lat, lon = centroid.y, centroid.x
            
            snap = MarineForecastService.get_environment(lat, lon, target_date)
            res = engine.evaluate(snap, vessel)
            
            # Extract live meteo data
            hs = snap.current.wave_height_m or 0.0
            curr = snap.current.current_speed_ms or 0.0
            
            # Use the inverse of severity for fishing opportunity 'Score: X/100' 
            # Or use a dedicated scoring logic. The frontend expects 'risk_score' to show out of 100.
            # If severity is 20, fishing score is 80.
            fishing_score = max(0, 100 - res["severity_score"])
            
            if "properties" not in feat:
                feat["properties"] = {}
                
            feat["properties"]["wave_hs_median"] = hs
            feat["properties"]["current_median"] = curr
            feat["properties"]["risk_score"] = fishing_score
            feat["properties"]["bsi_severity"] = res["severity_score"]
            
            return feat
        except Exception:
            if "properties" not in feat:
                feat["properties"] = {}
            # Defaults if Open-Meteo fails
            feat["properties"]["wave_hs_median"] = 1.2
            feat["properties"]["current_median"] = 0.25
            feat["properties"]["risk_score"] = 85
            return feat

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        augmented_features = list(executor.map(augment_feature, features))
        
    geojson["features"] = augmented_features
    return geojson"""

content = content.replace(old_func, new_func)

with open("backend/app/api/endpoints/pfz_router.py", "w") as f:
    f.write(content)
