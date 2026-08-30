from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.enums import TripDecision, RiskLevel

class RouteSnapshot(BaseModel):
    time: datetime
    lat: float
    lon: float
    wave_height_m: float
    wind_speed_kmh: float
    wind_direction_deg: float
    current_speed_ms: float
    current_direction_deg: float
    bsi: int
    risk: RiskLevel

class RouteSegment(BaseModel):
    segment_index: int
    coordinates: List[List[float]]
    risk: RiskLevel
    reason: Optional[str] = None

class RecommendedTrip(BaseModel):
    id: str
    travel_time_hours: float
    route_coords: List[List[float]]
    snapshots: List[RouteSnapshot]
    segments: List[RouteSegment]

class AlternativeTrip(BaseModel):
    pfz_id: str
    status: str
    reason: str

class TripAnalysisResponse(BaseModel):
    decision: TripDecision
    recommended_pfz: Optional[RecommendedTrip] = None
    decision_reasons: List[dict] = []
    alternatives: List[AlternativeTrip] = []
