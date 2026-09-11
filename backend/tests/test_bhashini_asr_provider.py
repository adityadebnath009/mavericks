import os

import pytest

from app.agents.providers.bhashini_asr_provider import BhashiniAsrProvider


def test_transcript_reads_pipeline_asr_source():
    assert BhashiniAsrProvider._transcript({"pipelineResponse": [{"output": [{"source": "नमस्ते"}]}]}) == "नमस्ते"


def test_service_ids_cover_console_languages(monkeypatch):
    monkeypatch.delenv("BHASHINI_ASR_EN_SERVICE_ID", raising=False)
    monkeypatch.delenv("BHASHINI_ASR_INDO_ARYAN_SERVICE_ID", raising=False)
    assert BhashiniAsrProvider._service_id("en-IN") == "ai4bharat/whisper-medium-en--gpu--t4"
    assert BhashiniAsrProvider._service_id("hi-IN") == "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
    assert BhashiniAsrProvider._service_id("mr-IN") == "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"


@pytest.mark.asyncio
async def test_asr_never_attempts_network_without_inference_key(monkeypatch):
    monkeypatch.delenv("BHASHINI_INFERENCE_KEY", raising=False)
    result = await BhashiniAsrProvider().transcribe("UklGRiQAAABXQVZF", "hi-IN")
    assert result["state"] == "UNAVAILABLE"
    assert "configured" in result["reason"]
