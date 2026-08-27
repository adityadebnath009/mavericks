from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.services.pfz_intelligence import PFZIntelligenceService
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.pfz_routing import PFZRoutingService

router = APIRouter()

class VesselLocation(BaseModel):
    lat: float
    lon: float

class PFZEvaluationRequest(BaseModel):
    vessel: VesselLocation
    pfz_id: str
    beam_m: float = 3.5

class PFZRouteRequest(BaseModel):
    start: VesselLocation
    end: VesselLocation
    beam_m: float = 3.5
    day: int = 1
    hour: int = 12

@router.get("")
@router.get("/")
def get_pfz_lines():
    """
    Retrieves the raw WFS GeoJSON features representing Potential Fishing Zones.
    """
    try:
        return INCOISGeoServerClient.get_pfz_lines_wfs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            day=request.day,
            hour=request.hour,
            db=db
        )
        return res
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
