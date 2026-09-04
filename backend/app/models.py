from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PipelineResult(BaseModel):
    """
    Result produced by the Planner Agent after coordinating
    the specialist agent pipelines.
    """

    orchestration_status: str

    active_mode: str

    total_latency_ms: Optional[float] = None

    is_stale_fallback: bool = Field(
        default=False,
        description="True if fallback cache data exceeds the freshness threshold."
    )

    system_advisory_warning: Optional[str] = Field(
        default=None,
        description="Warning related to stale or fallback data."
    )

    weather_payload: Dict[str, Any]

    ocean_payload: Dict[str, Any]