"""Bounded, evidence-grounded OpenAI narration for the Intelligence Console.

This provider never selects an intent or computes an operational decision.  It
receives a compact, already-validated Console payload and can only improve the
human-facing explanation around that payload.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import httpx
from app.config import settings


class OpenAIExplanationProvider:
    """Generate a fisherman-language narrative without exposing credentials."""

    _default_model = "gpt-4o-mini"
    _timeout_seconds = 14.0

    @staticmethod
    def _text(value: Any, limit: int = 420) -> str:
        return value.strip()[:limit] if isinstance(value, str) else ""

    @classmethod
    def _evidence_brief(cls, payload: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Whitelist only compact fields that are safe for a narrative prompt."""
        execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        synthesis = payload.get("synthesis") if isinstance(payload.get("synthesis"), dict) else {}
        map_data = payload.get("mapData") if isinstance(payload.get("mapData"), dict) else {}
        safety = map_data.get("safetyEvidence") if isinstance(map_data.get("safetyEvidence"), dict) else {}
        weather = safety.get("weather") if isinstance(safety.get("weather"), dict) else {}
        marine = safety.get("marine") if isinstance(safety.get("marine"), dict) else {}
        geofence = map_data.get("geofence") or safety.get("geofence")
        if not isinstance(geofence, dict):
            geo_safeguards = (map_data.get("explainability") or {}).get("safeguards", [])
            geofence = next((item for item in geo_safeguards if isinstance(item, dict) and item.get("label") == "Geofence"), {})

        def sources() -> list[Dict[str, Any]]:
            result = []
            for source in execution.get("sourceStatus") or []:
                if not isinstance(source, dict):
                    continue
                result.append({key: source.get(key) for key in ("source", "state", "fetchedAt", "ageHours", "cacheAgeSeconds", "reason") if source.get(key) is not None})
            return result[:12]

        pfz = []
        for point in map_data.get("pfzPoints") or []:
            if isinstance(point, dict):
                properties = point.get("properties") if isinstance(point.get("properties"), dict) else {}
                pfz.append({"lat": point.get("lat"), "lon": point.get("lon"), "distanceKm": properties.get("distanceKm"), "freshness": properties.get("freshness")})
        route = map_data.get("activeRoute") if isinstance(map_data.get("activeRoute"), dict) else {}
        route_info = route.get("route") if isinstance(route.get("route"), dict) else {}
        citations = []
        for paper in payload.get("ragFootnotes") or []:
            if isinstance(paper, dict):
                citations.append({"title": cls._text(paper.get("title"), 180), "url": paper.get("landingPageUrl") or paper.get("doi")})
        return {
            "userQuery": cls._text(query, 600),
            "intent": payload.get("intent"),
            "assessment": payload.get("assessment"),
            "certification": payload.get("certification"),
            "deterministicSummary": cls._text(synthesis.get("executive_summary"), 900),
            "deterministicHazards": [cls._text(item.get("text") if isinstance(item, dict) else item, 180) for item in synthesis.get("identified_hazards", []) or []][:6],
            "deterministicDirectives": [cls._text(item.get("text") if isinstance(item, dict) else item, 180) for item in synthesis.get("operational_directives", []) or []][:4],
            "sources": sources(),
            "weather": {key: weather.get(key) for key in ("windSpeedKmh", "windGustKmh", "visibilityM", "precipitationProbability", "state") if weather.get(key) is not None},
            "marine": {key: marine.get(key) for key in ("waveHeightM", "swellHeightM", "windWaveHeightM", "currentSpeedMs", "seaLevelHeightMslM", "seaSurfaceTemperatureC", "state") if marine.get(key) is not None},
            "geofence": {key: geofence.get(key) for key in ("status", "message", "meaning", "effect", "boundary", "distanceKm") if geofence.get(key) is not None},
            "pfz": pfz[:3],
            "route": {key: route_info.get(key) for key in ("distance_km", "duration_hours") if route_info.get(key) is not None},
            "citations": citations[:6],
        }

    @staticmethod
    def _validated_narrative(value: Any) -> Dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        summary = value.get("plain_summary")
        advisory = value.get("fisherman_advisory")
        if not isinstance(summary, str) or not summary.strip() or not isinstance(advisory, dict):
            return None
        headline = advisory.get("headline")
        if not isinstance(headline, str) or not headline.strip():
            return None
        reasons = []
        for item in advisory.get("reasons") or []:
            if isinstance(item, dict) and isinstance(item.get("title"), str) and isinstance(item.get("text"), str):
                reasons.append({"title": item["title"].strip()[:120], "text": item["text"].strip()[:260]})
        actions = [item.strip()[:220] for item in advisory.get("actions") or [] if isinstance(item, str) and item.strip()]
        followups = [item.strip()[:180] for item in value.get("followups") or [] if isinstance(item, str) and item.strip()]
        limitations = [item.strip()[:220] for item in value.get("limitations") or [] if isinstance(item, str) and item.strip()]
        if not reasons or not actions:
            return None
        return {
            "plain_summary": summary.strip()[:850],
            "what_it_means": OpenAIExplanationProvider._text(value.get("what_it_means"), 360),
            "fisherman_advisory": {"headline": headline.strip()[:220], "reasons": reasons[:3], "actions": actions[:3]},
            "limitations": limitations[:3],
            "followups": followups[:3],
        }

    async def narrate(self, payload: Dict[str, Any], query: str) -> Dict[str, Any]:
        started = time.perf_counter()
        # Settings reads backend/.env even when Uvicorn was launched without
        # exporting variables into the shell environment.
        model = os.getenv("OPENAI_NARRATIVE_MODEL") or settings.OPENAI_NARRATIVE_MODEL or self._default_model
        api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key:
            return {"state": "UNAVAILABLE", "model": model, "latencyMs": 0, "reason": "OpenAI narrative service is not configured."}
        evidence = self._evidence_brief(payload, query)
        prompt = (
            "You are NAVIK's fisherman-language explanation assistant. Return JSON only. "
            "Use ONLY the EVIDENCE JSON below. Never alter assessment, certification, source state, coordinates, distance, route, restrictions, or citations. "
            "Do not state or imply that an official IMD warning is clear, verified, or absent unless EVIDENCE says it is. "
            "Do not call modeled precipitation a confirmed lightning or cyclone alert. "
            "For research, state that correlation does not establish causation. "
            "For a stale or missing chlorophyll layer, say regional ranking is unavailable. "
            "For destination-required routes, request a map destination; do not invent one. "
            "Keep language simple and actionable for a coastal fisher. "
            "Schema: {plain_summary:string, what_it_means:string, fisherman_advisory:{headline:string,reasons:[{title:string,text:string}],actions:[string]}, limitations:[string], followups:[string]}. "
            "Provide 1-3 reasons and 1-3 actions.\nEVIDENCE=" + json.dumps(evidence, ensure_ascii=False, default=str)
        )
        request_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You explain validated marine evidence. You never create evidence or operational decisions."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=request_payload,
                )
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            narrative = self._validated_narrative(json.loads(content))
            if narrative is None:
                return {"state": "UNAVAILABLE", "model": model, "latencyMs": round((time.perf_counter() - started) * 1000, 2), "reason": "OpenAI returned an incomplete narrative schema."}
            return {"state": "LIVE", "model": model, "latencyMs": round((time.perf_counter() - started) * 1000, 2), "narrative": narrative, "evidenceContract": "VALIDATED_CONSOLE_EVIDENCE_ONLY"}
        except httpx.TimeoutException:
            reason = "OpenAI narrative request timed out."
        except httpx.HTTPStatusError as exc:
            reason = f"OpenAI returned HTTP {exc.response.status_code}."
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            reason = "OpenAI returned an unreadable narrative response."
        except Exception:
            reason = "OpenAI narrative request failed."
        return {"state": "UNAVAILABLE", "model": model, "latencyMs": round((time.perf_counter() - started) * 1000, 2), "reason": reason}
