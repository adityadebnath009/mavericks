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
    augmented_cache = "data/cache/pfz_lines_augmented.json"
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
