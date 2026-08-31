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
            cruising_speed_kn=request.cruising_speed_kn,
            departure_time=request.departure_time,
            db=db
        )
        return res
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except DataUnavailableError as due:
        raise HTTPException(status_code=503, detail=str(due))
    except NoSafeRouteError as nsr:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=200, content={"error": "REJECTED_NO_SAFE_ROUTE", "message": str(nsr)})
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
