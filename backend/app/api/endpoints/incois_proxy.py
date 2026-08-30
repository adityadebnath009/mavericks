from fastapi import APIRouter, Query, HTTPException
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.pfz_enricher import PFZEnricherService

router = APIRouter()

@router.get("/capabilities")
@router.get("/capabilities/")
def get_incois_capabilities():
    """
    Proxies and parses the GetCapabilities XML document from the official
    INCOIS GeoServer, returning currently available layers in JSON format.
    """
    return INCOISGeoServerClient.get_capabilities()

@router.get("/feature-info")
@router.get("/feature-info/")
def inspect_coordinate_feature(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude of point to inspect"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude of point to inspect"),
    layer: str = Query(..., description="Layer name to inspect (e.g. PFZ-TUNA-SST-CHL:sst)")
):
    """
    Performs a GetFeatureInfo coordinate-level query to fetch the numeric
    observation values associated with the clicked point.
    """
    res = INCOISGeoServerClient.get_feature_info(lat, lon, layer)
    if res.get("status") == "error":
        raise HTTPException(status_code=502, detail=res.get("message"))
    return res

@router.get("/point-analytics")
@router.get("/point-analytics/")
def get_point_analytics(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude coordinate of oceanic point"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude coordinate of oceanic point")
):
    """
    Spatiotemporal sampling endpoint returning timestamped environmental telemetry
    (SST, Chlorophyll, Wind, Surface Current, Waves) with multi-tier failsafe caching.
    """
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
    Proxies the WFS GeoJSON request to retrieve dynamic PFZ lines,
    enriched with multi-point environmental medians (SST, CHL, Wave, Current, Wind)
    and zero static species inference.
    """
    global _pfz_cache, _pfz_cache_time
    import time
    now = time.time()
    if _pfz_cache and (now - _pfz_cache_time) < 3600:
        return _pfz_cache

    try:
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        _pfz_cache = PFZEnricherService.enrich_feature_collection(raw_geojson)
        _pfz_cache_time = now
        return _pfz_cache
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enrich PFZ lines: {str(e)}")

@router.get("/vector-grid")
@router.get("/vector-grid/")
def get_vector_grid(
    day: int = Query(1, ge=1, le=3),
    hour: int = Query(12, ge=0, le=21, description="Forecast hour in 3-hour UTC steps")
):
    """
    Returns a gridded vector field of Wind and Currents for the exact
    forecast day/hour requested by the frontend.
    """
    if hour % 3 != 0:
        raise HTTPException(status_code=400, detail="hour must be one of 0, 3, 6, 9, 12, 15, 18, or 21")

    try:
        from app.api.services.incois_resolver import IncoisDatasetResolver
        return IncoisDatasetResolver.resolve_vector_grid(day=day, hour=hour)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector grid generation failed: {str(e)}")

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
    """
    Proxies WMS tile requests to INCOIS GeoServer to bypass frontend CORS restrictions.
    """
    from fastapi.responses import Response
    import requests

    incois_url = "https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms"
    params = {
        "service": service,
        "request": request,
        "layers": layers,
        "styles": styles,
        "format": format,
        "transparent": transparent,
        "version": version,
        "width": width,
        "height": height,
        "srs": srs,
        "bbox": bbox
    }

    try:
        res = requests.get(incois_url, params=params, timeout=10)
        res.raise_for_status()
        return Response(content=res.content, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WMS Proxy failed: {str(e)}")
