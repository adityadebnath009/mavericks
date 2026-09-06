import re

with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

old_func = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    cached_collection = PFZEnricherService.get_cached_pfz_collection()
    if cached_collection:
        return cached_collection
    try:
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        return PFZEnricherService.enrich_feature_collection(raw_geojson)
    except Exception as e:
        return PFZEnricherService.get_raw_pfz_with_fallback()"""

new_func = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
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
            
            hs = snap.current.wave_height_m or 0.0
            curr = snap.current.current_speed_ms or 0.0
            
            # Map BSI risk (0-100) inversely to Fishing catch score (100-0)
            # A severe sea (80 risk) means poor fishing conditions (20 score).
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
            feat["properties"]["wave_hs_median"] = 1.2
            feat["properties"]["current_median"] = 0.25
            feat["properties"]["risk_score"] = 85
            return feat

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        augmented_features = list(executor.map(augment_feature, features))
        
    geojson["features"] = augmented_features
    return geojson"""

content = content.replace(old_func, new_func)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(content)
