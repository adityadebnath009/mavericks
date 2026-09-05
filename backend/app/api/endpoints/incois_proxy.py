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
    cached_collection = PFZEnricherService.get_cached_pfz_collection()
    if cached_collection:
        return cached_collection
    try:
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        return PFZEnricherService.enrich_feature_collection(raw_geojson)
    except Exception as e:
        return PFZEnricherService.get_raw_pfz_with_fallback()

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

    incois_url = "https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms"
    params = {"service": service, "request": request, "layers": layers, "styles": styles, "format": format, "transparent": transparent, "version": version, "width": width, "height": height, "srs": srs, "bbox": bbox}
    try:
        res = requests.get(incois_url, params=params, timeout=30)
        res.raise_for_status()
        return Response(content=res.content, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WMS Proxy failed: {str(e)}")
