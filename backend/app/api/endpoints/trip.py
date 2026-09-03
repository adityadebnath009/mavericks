from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List
from datetime import datetime

from app.db.session import get_db
from app.api.services.trip_decision import TripDecisionEngine
from app.schemas.routing import TripAnalysisResponse

router = APIRouter()

class Coordinate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class Vessel(BaseModel):
    beam_m: float = Field(default=3.5, description="Vessel beam width in meters")
    length_m: float = Field(default=10.0, description="Vessel overall length in meters")
    cruising_speed_kn: float = Field(default=8.0, gt=0, description="Cruising speed in knots")

class TripRequest(BaseModel):
    start: Coordinate
    departure_time: str = Field(description="Departure timestamp (ISO format, e.g. 2026-08-29T06:00:00)")
    vessel: Vessel = Field(default_factory=Vessel)

    @field_validator("departure_time")
    @classmethod
    def validate_departure_time(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("departure_time must be a valid ISO-8601 string")
        return v

@router.post("/analyze", response_model=TripAnalysisResponse)
def analyze_trip(request: TripRequest, db: Session = Depends(get_db)):
    """
    Orchestrated Spatio-Temporal Trip Analysis Endpoint.
    Evaluates weather, currents, geofencing, and capsizing risks to recommend optimal routes and safety windows.
    """
    result = TripDecisionEngine.analyze_trip(
        start_lat=request.start.lat,
        start_lon=request.start.lon,
        departure_time=request.departure_time,
        beam_m=request.vessel.beam_m,
        length_m=request.vessel.length_m,
        cruising_speed_kn=request.vessel.cruising_speed_kn,
        db=db
    )
    
    # Valid request + safe route OR Valid request + no feasible route
    # Both represent a mathematically valid domain evaluation and should return 200 OK
    return result
