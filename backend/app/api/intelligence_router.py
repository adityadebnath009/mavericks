"""AI-only API surface for the Intelligence Console.

This router intentionally contains the Console contract only.  Heavy agent
imports happen inside the request handler, keeping existing operations routes
available even if an optional Console provider is unavailable.
"""
from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, IntelligencePipelineResult


intelligence_router = APIRouter(tags=["Intelligence Console"])


@intelligence_router.post("/chat", response_model=IntelligencePipelineResult)
async def process_chat_query(request: ChatRequest):
    """Run the isolated Intelligence Console orchestration flow."""
    try:
        from app.agents.intelligence_orchestrator import IntelligenceOrchestrator

        orchestrator = IntelligenceOrchestrator()
        return await orchestrator.run(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
