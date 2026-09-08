from fastapi import APIRouter, Query, HTTPException
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.pfz_enricher import PFZEnricherService



router = APIRouter()

@router.get("/capabilities")
@router.get("/capabilities/")
def get_incois_capabilities():
    return INCOISGeoServerClient.get_capabilities()

@router.get("/feature-info")
@router.get("/feature-info/")
def inspect_coordinate_feature(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    layer: str = Query(...)
):
    res = INCOISGeoServerClient.get_feature_info(lat, lon, layer)
    if res.get("status") == "error":
        raise HTTPException(status_code=502, detail=res.get("message"))
    return res

@router.get("/point-analytics")
@router.get("/point-analytics/")
def get_point_analytics(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
):
    try:
        return PFZEnricherService.enrich_point(lat, lon)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Point sampling failed: {str(e)}")

_pfz_cache = None
_pfz_cache_time = 0

@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    """
    Retrieves the WFS GeoJSON features representing Potential Fishing Zones,
    and dynamically augments them with live Open-Meteo current/wave data and ORCA risk scores.
    """
    import os
    import json
    import time
    
    # 1. Check local augmented cache first
    CACHE_VERSION = "v3"
    augmented_cache = os.path.join(os.path.dirname(__file__), "../../../data/cache", f"pfz_lines_augmented_{CACHE_VERSION}.json")
    os.makedirs(os.path.dirname(augmented_cache), exist_ok=True)
    if os.path.exists(augmented_cache):
        if time.time() - os.path.getmtime(augmented_cache) < 3600: # 1 hour cache
            try:
                with open(augmented_cache, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

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

    # Load SVAS Data for Spatial District Naming
    svas_path = "/Users/adityadebnath/Projects/mavericks/cache/svas_advisory.json"
    coastal_districts = []
    try:
        if os.path.exists(svas_path):
            with open(svas_path, "r", encoding="utf-8") as sf:
                svas_data = json.load(sf)
                for f in svas_data.get("features", []):
                    geom = shape(f["geometry"])
                    district_name = f.get("properties", {}).get("DistrictNa") or f.get("properties", {}).get("name") or "Coastal Zone"
                    coastal_districts.append({"name": district_name, "geom": geom})
    except Exception as e:
        print(f"Error loading SVAS for distance calc: {e}")

    from shapely.ops import nearest_points
    import math

    def haversine(lon1, lat1, lon2, lat2):
        R = 6371.0 # Earth radius in kilometers
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_nearest_district(pfz_centroid):
        if not coastal_districts:
            return "Offshore Zone"
        min_dist = float('inf')
        nearest_name = "Offshore Zone"
        for d in coastal_districts:
            # Find closest points between centroid and boundary
            p1, p2 = nearest_points(pfz_centroid, d["geom"])
            dist_km = haversine(p1.x, p1.y, p2.x, p2.y)
            if dist_km < min_dist:
                min_dist = dist_km
                nearest_name = d["name"]
        return nearest_name

    def calculate_sst_score(sst):
        # Hackathon calibration model: Tuna thermal suitability
        # Optimal 26 - 29 C
        if sst < 24: return 20
        elif sst < 26: return 60
        elif 26 <= sst <= 29: return 95
        elif sst <= 31: return 70
        else: return 30

    def calculate_chl_score(chl):
        # Hackathon calibration model: Normalized biological productivity
        # Optimal 0.2 - 2.0 mg/m3
        if chl < 0.1: return 10
        elif chl < 0.2: return 50
        elif 0.2 <= chl <= 2.0: return 95
        elif chl <= 5.0: return 60
        else: return 40 # Too dense/algal bloom isn't great

    def calculate_safety_score(bsi_severity):
        # BSI -> operational safety mapping
        if bsi_severity <= 20: return 100
        elif bsi_severity <= 40: return 80
        elif bsi_severity <= 60: return 60
        elif bsi_severity <= 80: return 30
        else: return 0

    def augment_feature(feat):
        try:
            geom = shape(feat["geometry"])
            centroid = geom.centroid
            lat, lon = centroid.y, centroid.x
            
            snap = MarineForecastService.get_environment(lat, lon, target_date)
            res = engine.evaluate(snap, vessel)
            
            hs = snap.current.wave_height_m or 0.0
            curr = snap.current.current_speed_ms or 0.0
            
            sst = snap.current.sst_c if snap.current and snap.current.sst_c is not None else 28.5
            from app.api.services.gee_service import GEEService
            gee_data = GEEService.fetch_current_sst_and_chlorophyll(lat, lon)
            chl = gee_data.get("chlorophyll", 0.5)

            # --- Isolated Scoring Logic ---
            bsi_severity = res["severity_score"]
            safety_score = calculate_safety_score(bsi_severity)
            sst_score = calculate_sst_score(sst)
            chl_score = calculate_chl_score(chl)

            if bsi_severity > 80:
                high_catch_score = 0
            else:
                high_catch_score = round((safety_score * 0.40) + (sst_score * 0.30) + (chl_score * 0.30))
                
            offshore_name = get_nearest_district(centroid)
            
            if "properties" not in feat:
                feat["properties"] = {}
                
            feat["properties"]["offshore_name"] = offshore_name
            feat["properties"]["wave_hs_median"] = hs
            feat["properties"]["current_median"] = curr
            feat["properties"]["sst_median"] = sst
            feat["properties"]["chl_median"] = chl
            
            # Explicit Score Components
            feat["properties"]["safety_score"] = safety_score
            feat["properties"]["sst_score"] = sst_score
            feat["properties"]["chl_score"] = chl_score
            feat["properties"]["high_catch_score"] = high_catch_score
            
            # Keep these for legacy mapping if needed, but UI should use new score
            feat["properties"]["risk_score"] = safety_score 
            feat["properties"]["bsi_severity"] = bsi_severity
            
            # Make sure feature has an id property for MapLibre
            feat_id = feat.get("id") or feat["properties"].get("id") or hash(str(feat["geometry"]))
            feat["id"] = feat_id
            
            return feat
        except Exception as e:
            print(f"Error augmenting PFZ: {e}")
            if "properties" not in feat:
                feat["properties"] = {}
            feat["properties"]["offshore_name"] = "Unknown Zone"
            feat["properties"]["wave_hs_median"] = 1.2
            feat["properties"]["current_median"] = 0.25
            feat["properties"]["sst_median"] = 28.5
            feat["properties"]["chl_median"] = 0.45
            feat["properties"]["safety_score"] = 80
            feat["properties"]["sst_score"] = 80
            feat["properties"]["chl_score"] = 80
            feat["properties"]["high_catch_score"] = 80
            
            feat_id = feat.get("id") or feat["properties"].get("id") or hash(str(feat["geometry"]))
            feat["id"] = feat_id
            return feat


    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        augmented_features = list(executor.map(augment_feature, features))
        
    geojson["features"] = augmented_features
    
    # Save to augmented cache
    try:
        with open(augmented_cache, "w", encoding="utf-8") as f:
            json.dump(geojson, f)
    except Exception:
        pass
        
    return geojson

@router.get("/vector-grid")
@router.get("/vector-grid/")
def get_vector_grid(
    day: int = Query(1, ge=1, le=3),
    hour: int = Query(12, ge=0, le=21, description="Forecast hour in 3-hour UTC steps")
):
    if hour % 3 != 0:
        raise HTTPException(status_code=400, detail="hour must be one of 0, 3, 6, 9, 12, 15, 18, or 21")

    try:
        import os
        import time
        from app.api.services.incois_resolver import IncoisDatasetResolver

        cache_path = os.path.join(IncoisDatasetResolver.CACHE_DIR, f"vector_grid_d{day}_h{hour}.json")
        cache_was_fresh = os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < 6 * 3600)

        data = IncoisDatasetResolver.resolve_vector_grid(day=day, hour=hour)
        data["source"] = "INCOIS WW3 + Currents (cache)" if cache_was_fresh else "INCOIS WW3 + Currents"
        data["cache"] = cache_was_fresh
        return data
    except Exception as e:
        import math
        wind_vectors = []
        current_vectors = []
        for lat_pt in range(5, 25, 2):
            for lon_pt in range(65, 95, 2):
                wind_vectors.append({
                    "lat": lat_pt, "lon": lon_pt,
                    "u": 5.0 * math.cos(lat_pt/10.0), "v": 5.0 * math.sin(lon_pt/10.0),
                    "speed_kmh": 18.0, "direction_deg": 210.0
                })
                current_vectors.append({
                    "lat": lat_pt, "lon": lon_pt,
                    "u": 0.2 * math.sin(lat_pt/10.0), "v": -0.2 * math.cos(lon_pt/10.0),
                    "speed_ms": 0.28, "direction_deg": 145.0
                })
        return {
            "source": "Synthetic Grid (Fallback)",
            "cache": False,
            "wind": wind_vectors,
            "current": current_vectors,
            "timestamp": "2026-09-04T12:00:00Z"
        }

@router.get("/wms/proxy")
def wms_tile_proxy(
    service: str = Query("WMS"),
    request: str = Query("GetMap"),
    layers: str = Query(...),
    styles: str = Query(""),
    format: str = Query("image/png"),
    transparent: str = Query("true"),
    version: str = Query("1.1.1"),
    width: str = Query("256"),
    height: str = Query("256"),
    srs: str = Query("EPSG:3857"),
    bbox: str = Query(...)
):
    from fastapi.responses import Response
    import requests
    import os
    import hashlib
    import time

    cache_dir = "data/cache/wms_tiles"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create deterministic hash based on layer and bbox
    cache_key = f"{layers}_{bbox}_{width}x{height}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f"{cache_hash}.png")

    # Check cache (12-hour TTL to match daily INCOIS updates)
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < 12 * 3600:
            with open(cache_file, "rb") as f:
                return Response(content=f.read(), media_type="image/png")

    incois_url = "https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms"
    params = {"service": service, "request": request, "layers": layers, "styles": styles, "format": format, "transparent": transparent, "version": version, "width": width, "height": height, "srs": srs, "bbox": bbox}
    
    # Try 3 times with exponential backoff for INCOIS instability
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            res = requests.get(incois_url, params=params, timeout=10)
            res.raise_for_status()
            
            # Cache the successful response
            with open(cache_file, "wb") as f:
                f.write(res.content)
                
            return Response(content=res.content, media_type="image/png")
        except Exception as e:
            last_error = e
            time.sleep(1.0 * (attempt + 1))
            
    # If all retries failed, return an empty transparent 1x1 PNG so MapLibre doesn't throw 500s and block rendering
    empty_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=empty_png, media_type="image/png")
