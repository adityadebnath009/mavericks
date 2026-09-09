"""OpenAlex literature evidence for the Intelligence Console only.

OpenAlex is a scholarly index, not an operational marine observation source.
This provider therefore returns traceable papers as supporting context and
never turns a paper into a safety or fishing recommendation by itself.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import httpx


class OpenAlexResearchProvider:
    _url = "https://api.openalex.org/works"
    _cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _ttl_seconds = 6 * 60 * 60

    @staticmethod
    def _paper(work: Dict[str, Any]) -> Dict[str, Any]:
        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        open_access = work.get("open_access") or {}
        best_oa = work.get("best_oa_location") or {}
        return {
            "id": work.get("id"),
            "title": work.get("title") or "Untitled work",
            "publicationDate": work.get("publication_date"),
            "citationCount": work.get("cited_by_count"),
            "doi": work.get("doi"),
            "source": source.get("display_name"),
            "landingPageUrl": best_oa.get("landing_page_url") or location.get("landing_page_url"),
            "isOpenAccess": bool(open_access.get("is_oa")),
        }

    async def search(self, query: str, limit: int = 4) -> Dict[str, Any]:
        # Retain enough wording to search the research question, while bounding
        # an untrusted conversational string before placing it in a URL.
        key = " ".join(query.split())[:500].lower()
        cached = self._cache.get(key)
        now = time.monotonic()
        age_seconds = round(now - cached[0], 1) if cached else None
        if cached and age_seconds <= self._ttl_seconds:
            return {**cached[1], "state": "CACHED", "cacheAgeSeconds": age_seconds}

        params: Dict[str, Any] = {
            "search": key,
            "filter": "type:article",
            "sort": "cited_by_count:desc",
            "per-page": min(max(limit, 1), 10),
            "select": "id,title,publication_date,cited_by_count,doi,primary_location,open_access,best_oa_location",
        }
        api_key = os.getenv("OPENALEX_API_KEY")
        if api_key:
            params["api_key"] = api_key
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(self._url, params=params)
                response.raise_for_status()
                works = response.json().get("results", [])
            payload = {
                "source": "openalex",
                "state": "LIVE",
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "cacheAgeSeconds": 0,
                "papers": [self._paper(work) for work in works if isinstance(work, dict)],
            }
            self._cache[key] = (now, payload)
            return payload
        except Exception as exc:
            if cached:
                return {**cached[1], "state": "STALE", "cacheAgeSeconds": age_seconds,
                        "reason": f"Live OpenAlex refresh failed: {exc}"}
            return {"source": "openalex", "state": "UNAVAILABLE", "reason": str(exc), "papers": []}
