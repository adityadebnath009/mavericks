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

@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    """
    Proxies the WFS GeoJSON request to retrieve dynamic PFZ lines,
    enriched with multi-point environmental medians (SST, CHL, Wave, Current, Wind)
    and zero static species inference.
    """
    try:
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        return PFZEnricherService.enrich_feature_collection(raw_geojson)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enrich PFZ lines: {str(e)}")

@router.get("/vector-grid")
@router.get("/vector-grid/")
def get_vector_grid(day: int = Query(1, ge=1, le=3)):
    """
    Returns a gridded vector field of Wind and Currents for MapLibre arrow rendering.
    """
    try:
        from app.api.services.incois_resolver import IncoisDatasetResolver
        return IncoisDatasetResolver.resolve_vector_grid(day=day)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector grid generation failed: {str(e)}")
