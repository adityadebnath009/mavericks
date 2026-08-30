from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ChatRequest(BaseModel):
    user_id: str = Field(default="guest")
    query: str = Field(..., description="The user's natural language question")
    latitude: float
    longitude: float

class PipelineResult(BaseModel):
    orchestration_status: str
    active_mode: str
    total_latency_ms: Optional[float] = None
    is_stale_fallback: bool = Field(default=False, description="True if fallback cache exceeds age limit")
    system_advisory_warning: Optional[str] = Field(default=None, description="Staleness or fallback advisory message")
    weather_payload: Dict[str, Any]
    ocean_payload: Dict[str, Any]