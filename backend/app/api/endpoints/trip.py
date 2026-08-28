from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from app.api.deps import get_db
from app.api.services.trip_decision import TripDecisionEngine

router = APIRouter()

class Coordinate(BaseModel):
    lat: float
    lon: float

class Vessel(BaseModel):
    beam_m: float = Field(default=3.5, description="Vessel beam width in meters")
    length_m: float = Field(default=10.0, description="Vessel overall length in meters")
    cruising_speed_kn: float = Field(default=8.0, description="Cruising speed in knots")

class TripRequest(BaseModel):
    start: Coordinate
    departure_time: str = Field(description="Departure timestamp (ISO format, e.g. 2026-08-29T06:00:00)")
    vessel: Vessel = Field(default_factory=Vessel)

@router.post("/analyze")
def analyze_trip(request: TripRequest, db: Session = Depends(get_db)):
    """
    Orchestrated Spatio-Temporal Trip Analysis Endpoint.
    Evaluates weather, currents, geofencing, and capsizing risks to recommend optimal routes and safety windows.
    """
    try:
        result = TripDecisionEngine.analyze_trip(
            start_lat=request.start.lat,
            start_lon=request.start.lon,
            departure_time=request.departure_time,
            beam_m=request.vessel.beam_m,
            length_m=request.vessel.length_m,
            cruising_speed_kn=request.vessel.cruising_speed_kn,
            db=db
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to analyze trip: {str(e)}")
