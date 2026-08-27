from fastapi import APIRouter, Query, HTTPException
from app.api.services.incois_geoserver import INCOISGeoServerClient

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
    lat: float = Query(..., description="Latitude of point to inspect"),
    lon: float = Query(..., description="Longitude of point to inspect"),
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

@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    """
    Proxies the WFS GeoJSON request to retrieve dynamic PFZ lines.
    Falls back to cached features if INCOIS GeoServer is down.
    """
    return INCOISGeoServerClient.get_pfz_lines_wfs()
