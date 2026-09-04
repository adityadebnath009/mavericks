from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List
from datetime import datetime

from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.orca_bsi_engine import VesselProfile

router = APIRouter()

class VesselLocation(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class VesselProfileInput(BaseModel):
    length_m: float = Field(default=8.0, gt=0)
    beam_m: float = Field(default=2.5, gt=0)
    cruising_speed_kn: float = Field(default=10.0, gt=0)

class RoutingRequest(BaseModel):
    origin: VesselLocation
    destination: VesselLocation
    vessel_profile: VesselProfileInput
    departure_time: str
    optimize_departure: bool = False

    @field_validator("departure_time")
    @classmethod
    def validate_departure_time(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("departure_time must be a valid ISO-8601 string")
        return v

@router.post("/safe-route")
def calculate_safe_route(request: RoutingRequest):
    """
    Calculates an optimal safe route using ORCA BSI engine and A* pathfinding.
    """
    v_profile = VesselProfile(
        length_m=request.vessel_profile.length_m,
        beam_m=request.vessel_profile.beam_m,
        cruising_speed_kn=request.vessel_profile.cruising_speed_kn
    )
    
    try:
        res = PFZRoutingService.calculate_optimal_route(
            start_lat=request.origin.lat,
            start_lon=request.origin.lon,
            end_lat=request.destination.lat,
            end_lon=request.destination.lon,
            vessel_profile=v_profile,
            departure_time=request.departure_time,
            optimize_departure=request.optimize_departure
        )
        if res is None:
            raise HTTPException(status_code=400, detail="No safe route found or invalid geofence constraints.")
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
