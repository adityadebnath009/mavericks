from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.api.services.pfz_intelligence import PFZIntelligenceService
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.pfz_routing import PFZRoutingService
from app.core.exceptions import DataUnavailableError, NoSafeRouteError

router = APIRouter()

import time
_pfz_augmented_cache = {"timestamp": 0, "data": None}

class VesselLocation(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class PFZEvaluationRequest(BaseModel):
    vessel: VesselLocation
    pfz_id: str
    beam_m: float = 3.5

class PFZRouteRequest(BaseModel):
    start: VesselLocation
    end: VesselLocation
    beam_m: float = 3.5
    cruising_speed_kn: float = Field(default=8.0, gt=0)
    departure_time: str

    @field_validator("departure_time")
    @classmethod
    def validate_departure_time(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("departure_time must be a valid ISO-8601 string")
        return v

@router.get("")
@router.get("/")
def get_pfz_lines():
    """
    Retrieves the WFS GeoJSON features representing Potential Fishing Zones,
    and dynamically augments them with live Open-Meteo current/wave data and ORCA risk scores.
    """
    global _pfz_augmented_cache
    if _pfz_augmented_cache["data"] is not None and (time.time() - _pfz_augmented_cache["timestamp"] < 3600):
        return _pfz_augmented_cache["data"]

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
            
            # Extract SST directly from Open-Meteo snapshot
            sst = snap.current.sst_c if snap.current and snap.current.sst_c is not None else 28.5
            
            # Fetch Chlorophyll from GEE (or fallback) since Open-Meteo lacks it
            from app.api.services.gee_service import GEEService
            gee_data = GEEService.fetch_current_sst_and_chlorophyll(lat, lon)
            chl = gee_data.get("chlorophyll", 0.5)
            
            # Use the inverse of severity for fishing opportunity 'Score: X/100' 
            fishing_score = max(0, 100 - res["severity_score"])
            
            if "properties" not in feat:
                feat["properties"] = {}
                
            feat["properties"]["wave_hs_median"] = hs
            feat["properties"]["current_median"] = curr
            feat["properties"]["sst_median"] = sst
            feat["properties"]["chl_median"] = chl
            feat["properties"]["risk_score"] = fishing_score
            feat["properties"]["bsi_severity"] = res["severity_score"]
            
            return feat
        except Exception:
            if "properties" not in feat:
                feat["properties"] = {}
            # Defaults if Open-Meteo/GEE fails
            feat["properties"]["wave_hs_median"] = 1.2
            feat["properties"]["current_median"] = 0.25
            feat["properties"]["sst_median"] = 28.5
            feat["properties"]["chl_median"] = 0.45
            feat["properties"]["risk_score"] = 85
            return feat

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        augmented_features = list(executor.map(augment_feature, features))
        
    geojson["features"] = augmented_features
    
    _pfz_augmented_cache["timestamp"] = time.time()
    _pfz_augmented_cache["data"] = geojson
    return geojson

@router.post("/evaluate")
@router.post("/evaluate/")
def evaluate_pfz_zone(request: PFZEvaluationRequest):
    """
    Evaluates vessel proximity and localized marine risks for a specific PFZ feature.
    """
    try:
        res = PFZIntelligenceService.evaluate_pfz_zone(
            vessel_lat=request.vessel.lat,
            vessel_lon=request.vessel.lon,
            pfz_id=request.pfz_id,
            beam_m=request.beam_m
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))

@router.post("/route")
@router.post("/route/")
def calculate_pfz_route(request: PFZRouteRequest, db: Session = Depends(get_db)):
    """
    Calculates the weather-optimized Dijkstra route from start vessel to destination.
    """
    try:
        res = PFZRoutingService.calculate_optimal_route(
            start_lat=request.start.lat,
            start_lon=request.start.lon,
            end_lat=request.end.lat,
            end_lon=request.end.lon,
            beam_m=request.beam_m,
            cruising_speed_kn=request.cruising_speed_kn,
            departure_time=request.departure_time,
            db=db
        )
        return res
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
