# app/models/intent.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ChatRequest(BaseModel):
    """The incoming payload from the React frontend."""
    text: str = Field(..., description="The transcribed voice text from the user.")
    language_code: str = Field("en-IN", description="The BCP-47 locale tag of the input.")
    current_lat: Optional[float] = Field(None, description="User's current GPS latitude.")
    current_lon: Optional[float] = Field(None, description="User's current GPS longitude.")

class ParsedIntent(BaseModel):
    """
    The deterministic output parsed by the LLM. 
    This acts as the strict input for the Planner Agent.
    """
    location_name: Optional[str] = Field(
        None, description="The specific beach, port, or PFZ mentioned (e.g., 'Puri Beach')."
    )
    departure_time: Optional[datetime] = Field(
        None, description="The intended departure time in ISO format."
    )
    activity_type: str = Field(
        default="fishing", 
        description="The marine activity, usually 'fishing', 'transit', or 'docked'."
    )
    vessel_size_meters: Optional[float] = Field(
        None, description="The size of the boat if mentioned (e.g., 12 for '12-meter boat')."
    )

class ChatResponse(BaseModel):
    """The final response sent back to the User Interaction Agent."""
    spoken_text: str = Field(..., description="The translated, concise advice for the TTS engine.")
    risk_score: int = Field(..., description="The calculated safety score from 0 to 100.")
    risk_label: str = Field(..., description="LOW, MODERATE, HIGH, or EXTREME.")
    extracted_intent: ParsedIntent = Field(..., description="The parameters extracted from the user.")