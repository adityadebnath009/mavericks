"""Console-only Bhashini translation adapter.

No translation is fabricated.  Deployments opt in by supplying the Bhashini
gateway URL and API key; without both, callers receive an explicit unavailable
state and retain the original English evidence text.
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx


class BhashiniTranslationProvider:
    _language_codes = {"hi-IN": "hi", "mr-IN": "mr"}

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
        endpoint = os.getenv("BHASHINI_TRANSLATION_URL")
        api_key = os.getenv("BHASHINI_API_KEY")
        if not endpoint or not api_key:
            return {"provider": "bhashini", "state": "UNAVAILABLE", "language": language,
                    "reason": "Bhashini credentials are not configured."}
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
