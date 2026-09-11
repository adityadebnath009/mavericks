from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from uuid import uuid4

class ChatRequest(BaseModel):
    user_id: str = Field(default="guest")
    query: str = Field(..., description="The user's natural language question")
    latitude: float
    longitude: float
    # Console route queries use an explicitly map-selected destination.  These
    # are optional so existing Console callers remain valid for point queries.
    destination_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    destination_lon: Optional[float] = Field(default=None, ge=-180, le=180)
    language: str = Field(default="en-IN")
    # A trace ID is mandatory for the Intelligence Console, but remains optional
    # for callers of the legacy contract.  Generating it here means an API caller
    # that does not provide one still gets an end-to-end traceable response.
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    history: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous conversational turns, e.g. [{'role': 'user', 'content': 'hi'}]")
    # Additive Intelligence Console context.  It is deliberately structured
    # and compact so callers never need to resend raw agent/provider payloads.
    conversation_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional prior Intelligence Console turn used to resolve natural follow-up questions.",
    )


class ConsoleTranscriptionRequest(BaseModel):
    """Bounded, Console-only microphone payload for server-side Bhashini ASR."""
    audio_base64: str = Field(..., min_length=32, max_length=7_000_000)
    language: str = Field(default="en-IN")

class PipelineResult(BaseModel):
    orchestration_status: str
    active_mode: str
    total_latency_ms: Optional[float] = None
    is_stale_fallback: bool = Field(default=False, description="True if fallback cache exceeds age limit")
    system_advisory_warning: Optional[str] = Field(default=None, description="Staleness or fallback advisory message")
    weather_payload: Dict[str, Any]
    ocean_payload: Dict[str, Any]
    agent_results: Optional[Dict[str, Any]] = Field(default=None, description="Raw outputs from all dynamically executed DAG agents")
    conversational_response: Optional[str] = Field(default=None, description="LLM synthesized natural language answer")
    suggested_queries: List[str] = Field(default_factory=list, description="0-3 contextual follow-up questions")


class IntelligencePipelineResult(BaseModel):
    """Direct V2 payload consumed only by the Intelligence Console."""
    request_id: Optional[str] = None
    state: str = "live"  # live | cached | error
    assessment: str = "UNKNOWN"
    certification: str = "UNVALIDATED"
    isSafetyFloorTriggered: bool = False
    synthesis: Dict[str, Any] = Field(default_factory=dict)
    evidenceMet: int = 0
    evidenceRequired: int = 0
    sources: List[str] = Field(default_factory=list)
    ragFootnotes: List[Any] = Field(default_factory=list)
    followups: List[str] = Field(default_factory=list)
    mapData: Dict[str, Any] = Field(default_factory=dict)
    execution: Dict[str, Any] = Field(default_factory=dict)
    intent: str = "general_marine"
    translation: Dict[str, Any] = Field(default_factory=dict)
