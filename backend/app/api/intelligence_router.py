"""AI-only API surface for the Intelligence Console.

This router intentionally contains the Console contract only.  Heavy agent
imports happen inside the request handler, keeping existing operations routes
available even if an optional Console provider is unavailable.
"""
from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ConsoleTranscriptionRequest, IntelligencePipelineResult


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


@intelligence_router.post("/chat/transcribe")
async def transcribe_console_audio(request: ConsoleTranscriptionRequest):
    """Transcribe Console microphone audio without exposing Bhashini credentials."""
    try:
        from app.agents.providers.bhashini_asr_provider import BhashiniAsrProvider

        result = await BhashiniAsrProvider().transcribe(request.audio_base64, request.language)
        if result.get("state") != "LIVE":
            raise HTTPException(status_code=503, detail=result.get("reason", "Speech transcription unavailable."))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Speech transcription failed.") from exc
