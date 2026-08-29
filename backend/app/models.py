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
    weather_payload: Dict[str, Any]
    ocean_payload: Dict[str, Any]