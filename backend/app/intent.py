from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Incoming user interaction from the frontend.
    """

    user_id: str = Field(
        default="guest",
        description="Identifier for the current user."
    )

    text: str = Field(
        ...,
        description="The user's natural language query or voice transcript."
    )

    language_code: str = Field(
        default="en-IN",
        description="BCP-47 locale tag of the user's input."
    )

    latitude: Optional[float] = Field(
        default=None,
        description="User's current GPS latitude."
    )

    longitude: Optional[float] = Field(
        default=None,
        description="User's current GPS longitude."
    )


class ParsedIntent(BaseModel):
    query_type: str = "marine_overview"

    activity_type: str = "fishing"

    location_name: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    departure_time: Optional[datetime] = None

    days_ahead: int = 0
    time_factor: float = 0.5

    vessel_size_meters: Optional[float] = None


class ChatResponse(BaseModel):
    """
    Final response returned to the frontend.
    """

    spoken_text: str = Field(
        ...,
        description="Human-friendly response suitable for display or TTS."
    )

    extracted_intent: ParsedIntent

    pipeline_result: Optional[dict] = Field(
        default=None,
        description="Raw pipeline output for frontend visualization."
    )