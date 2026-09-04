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
    """
    Structured interpretation of the user's request.

    This is produced by the User Interaction Agent and used to
    determine how the Planner Agent should be invoked.
    """

    location_name: Optional[str] = Field(
        default=None,
        description="Beach, port, fishing zone, or other location mentioned by the user."
    )

    departure_time: Optional[datetime] = Field(
        default=None,
        description="Intended departure time in ISO format."
    )

    activity_type: str = Field(
        default="fishing",
        description="Marine activity such as fishing, transit, or docked."
    )

    vessel_size_meters: Optional[float] = Field(
        default=None,
        description="Vessel size in meters, if mentioned."
    )


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