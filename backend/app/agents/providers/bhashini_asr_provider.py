"""Console-only Bhashini Udyat speech-to-text adapter.

Audio is accepted as an in-memory, mono PCM WAV payload.  Credentials are
read only on the server and are never returned to the browser.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv


# This provider can be invoked without the LLM orchestrator, so it cannot rely
# on that module's dotenv side effect to see the existing Udyat credentials.
load_dotenv()


class BhashiniAsrProvider:
    _language_codes = {"en-IN": "en", "hi-IN": "hi", "mr-IN": "mr"}
    _default_inference_url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    _default_service_ids = {
        "en-IN": "ai4bharat/whisper-medium-en--gpu--t4",
        "hi-IN": "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4",
        "mr-IN": "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4",
    }

    @staticmethod
    def _transcript(payload: Dict[str, Any]) -> str | None:
        """Read the documented and common pipeline response variants."""
        for key in ("text", "source", "transcript"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        pipeline = payload.get("pipelineResponse")
        if isinstance(pipeline, list):
            for item in pipeline:
                if not isinstance(item, dict):
                    continue
                output = item.get("output")
                if not isinstance(output, list):
                    continue
                for candidate in output:
                    if isinstance(candidate, dict):
                        for key in ("source", "text", "transcript"):
                            value = candidate.get(key)
                            if isinstance(value, str) and value.strip():
                                return value.strip()
        return None

    @classmethod
    def _service_id(cls, language: str) -> str | None:
        if language == "en-IN":
            return os.getenv("BHASHINI_ASR_EN_SERVICE_ID", cls._default_service_ids[language])
        if language in ("hi-IN", "mr-IN"):
            return os.getenv("BHASHINI_ASR_INDO_ARYAN_SERVICE_ID", cls._default_service_ids[language])
        return None

    async def transcribe(self, audio_content: str, language: str) -> Dict[str, Any]:
        source_language = self._language_codes.get(language)
        service_id = self._service_id(language)
        inference_key = os.getenv("BHASHINI_INFERENCE_KEY")
        if not source_language or not service_id:
            return {"provider": "bhashini_asr", "state": "UNAVAILABLE", "language": language,
                    "reason": "The selected Console language is unsupported."}
        if not inference_key:
            return {"provider": "bhashini_asr", "state": "UNAVAILABLE", "language": language,
                    "reason": "Bhashini speech recognition is not configured."}

        payload = {
            "pipelineTasks": [{
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": source_language},
                    "serviceId": service_id,
                    "samplingRate": 8000,
                    "audioFormat": "wav",
                    "encoding": None,
                },
            }],
            "inputData": {"audio": [{"audioContent": audio_content}]},
        }
        try:
            endpoint = os.getenv("BHASHINI_INFERENCE_URL", self._default_inference_url)
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(
                    endpoint,
                    headers={"Authorization": inference_key, "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                transcript = self._transcript(response.json())
            if not transcript:
                return {"provider": "bhashini_asr", "state": "UNAVAILABLE", "language": language,
                        "reason": "Bhashini returned no speech transcript.", "serviceId": service_id}
            return {"provider": "bhashini_asr", "state": "LIVE", "language": language,
                    "text": transcript, "serviceId": service_id}
        except Exception as exc:
            return {"provider": "bhashini_asr", "state": "UNAVAILABLE", "language": language,
                    "reason": f"Bhashini ASR inference failed: {exc}", "serviceId": service_id}
