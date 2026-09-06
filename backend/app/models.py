from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ChatRequest(BaseModel):
    user_id: str = Field(default="guest")
    query: str = Field(..., description="The user's natural language question")
    latitude: float
    longitude: float
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous conversational turns, e.g. [{'role': 'user', 'content': 'hi'}]")

class PipelineResult(BaseModel):
    orchestration_status: str
    active_mode: str
    total_latency_ms: Optional[float] = None
    is_stale_fallback: bool = Field(default=False, description="True if fallback cache exceeds age limit")
    system_advisory_warning: Optional[str] = Field(default=None, description="Staleness or fallback advisory message")
    weather_payload: Dict[str, Any]
    ocean_payload: Dict[str, Any]
    
    # New fields for Phase 7 Multi-Agent Orchestration
    agent_results: Optional[Dict[str, Any]] = Field(default=None, description="Raw outputs from all dynamically executed DAG agents")
    conversational_response: Optional[str] = Field(default=None, description="LLM synthesized natural language answer")
    suggested_queries: List[str] = Field(default_factory=list, description="0-3 contextual follow-up questions")