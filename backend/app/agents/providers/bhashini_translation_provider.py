"""Console-only Bhashini translation adapter.

Supports Bhashini Udyat's direct Pipeline Compute call.  The browser never
receives either key; unavailable translation leaves the evidence in English.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx


class BhashiniTranslationProvider:
    _language_codes = {"hi-IN": "hi", "mr-IN": "mr"}
    _default_inference_url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    @staticmethod
    def _translated_text(payload: Dict[str, Any]) -> str | None:
        """Accept the common Bhashini gateway response shapes defensively."""
        for key in ("translatedText", "translated_text", "text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        pipeline = payload.get("pipelineResponse")
        if isinstance(pipeline, list):
            for item in pipeline:
                if isinstance(item, dict):
                    output = item.get("output")
                    if isinstance(output, list) and output:
                        candidate = output[0]
                        if isinstance(candidate, dict) and isinstance(candidate.get("target"), str):
                            return candidate["target"].strip() or None
        return None

    async def translate(self, text: str, language: str) -> Dict[str, Any]:
        if language == "en-IN":
            return {"provider": "bhashini", "state": "NOT_REQUIRED", "language": language}
        target = self._language_codes.get(language)
        if not target:
            return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language,
                    "reason": "The selected Console language is unsupported."}
        inference_key = os.getenv("BHASHINI_INFERENCE_KEY")
        service_id = os.getenv("BHASHINI_NMT_SERVICE_ID")
        # Udyat's inference key is used directly with a chosen service ID.
        # The old generic gateway variables remain supported for deployments
        # that already use a custom Bhashini proxy.
        if inference_key and service_id:
            return await self._native_translate(text, language, target, inference_key, service_id)
        endpoint = os.getenv("BHASHINI_TRANSLATION_URL")
        api_key = os.getenv("BHASHINI_API_KEY")
        if not endpoint or not api_key:
            return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language,
                    "reason": "Bhashini translation service is not configured."}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"source_language": "en", "target_language": target, "text": text},
                )
                response.raise_for_status()
                translated = self._translated_text(response.json())
            if not translated:
                return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language,
                        "reason": "Bhashini returned no translated text."}
            return {"provider": "bhashini", "state": "LIVE", "language": language, "text": translated}
        except Exception as exc:
            return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language, "reason": str(exc)}

    async def _native_translate(self, text: str, language: str, target: str, inference_key: str, service_id: str) -> Dict[str, Any]:
        """Call the Udyat Pipeline Compute API for one NMT task."""
        endpoint = os.getenv("BHASHINI_INFERENCE_URL", self._default_inference_url)
        payload = {
            "pipelineTasks": [{
                "taskType": "translation",
                "config": {
                    "language": {"sourceLanguage": "en", "targetLanguage": target},
                    "serviceId": service_id,
                },
            }],
            "inputData": {"input": [{"source": text}]},
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(endpoint, headers={"Authorization": inference_key, "Content-Type": "application/json"}, json=payload)
                response.raise_for_status()
                translated = self._translated_text(response.json())
            if not translated:
                return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language,
                        "reason": "Bhashini returned no translated text."}
            return {"provider": "bhashini", "state": "LIVE", "language": language, "text": translated,
                    "serviceId": service_id}
        except Exception as exc:
            return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language,
                    "reason": f"Bhashini native inference failed: {exc}"}
