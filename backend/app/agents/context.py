from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import date
from dataclasses import field

class TemporalContext(BaseModel):
    mode: Literal["live", "historical"] = "live"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    resolution: Literal["hourly", "daily", "monthly", "annual"] = "monthly"
    analysis: List[Literal["trend", "anomaly", "comparison", "seasonality"]] = Field(default_factory=list)

class AgentContext(BaseModel):
    latitude: float
    longitude: float
    query: Optional[str] = None
    mode: str = "fisheries"
    time_range: Optional[Dict[str, str]] = None  # Legacy, to be removed if unused
    temporal: TemporalContext = Field(default_factory=TemporalContext)
    
    # Optional explicitly selected sub-features for the mode
    sub_features: Optional[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    prior_results: Dict[str, Any] = Field(default_factory=dict)
