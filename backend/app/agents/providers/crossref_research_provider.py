"""Crossref metadata fallback for Intelligence Console research only.

Crossref complements OpenAlex with canonical DOI and publisher metadata.  It
does not supply operational evidence and is never used outside `/api/chat`.
"""
from __future__ import annotations

import time
import os
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import httpx


class CrossrefResearchProvider:
    _url = "https://api.crossref.org/works"
    _cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _ttl_seconds = 6 * 60 * 60

    @staticmethod
    def _date(item: Dict[str, Any]) -> str | None:
        parts = (item.get("published-online") or item.get("published-print") or item.get("issued") or {}).get("date-parts") or []
        values = parts[0] if parts else []
        return "-".join(str(value).zfill(2) if index else str(value) for index, value in enumerate(values)) or None

    @classmethod
    def _paper(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        doi = item.get("DOI")
        links = item.get("link") or []
        full_text = next((link.get("URL") for link in links if isinstance(link, dict) and link.get("URL")), None)
        return {
            "id": f"https://doi.org/{doi}" if doi else item.get("URL"),
            "title": (item.get("title") or ["Untitled work"])[0],
            "publicationDate": cls._date(item),
            "citationCount": item.get("is-referenced-by-count"),
            "doi": f"https://doi.org/{doi}" if doi else None,
            "source": (item.get("container-title") or [None])[0],
            "landingPageUrl": full_text or item.get("URL") or (f"https://doi.org/{doi}" if doi else None),
            "isOpenAccess": bool(item.get("license")),
            "sources": ["crossref"],
        }

    async def search(self, query: str, limit: int = 4) -> Dict[str, Any]:
        key = " ".join(query.split())[:500].lower()
        cached = self._cache.get(key)
        now = time.monotonic()
        age = round(now - cached[0], 1) if cached else None
        if cached and age <= self._ttl_seconds:
            return {**cached[1], "state": "CACHED", "cacheAgeSeconds": age}
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                params = {"query.bibliographic": key, "rows": min(max(limit, 1), 10), "select": "DOI,title,published-online,published-print,issued,is-referenced-by-count,container-title,URL,link,license"}
                # The public endpoint remains free.  A project contact lets
                # Crossref place this service in its higher-limit polite pool.
                if mailto := os.getenv("CROSSREF_MAILTO"):
                    params["mailto"] = mailto
                response = await client.get(self._url, params=params, headers={"User-Agent": "ORCA-Intelligence-Console/1.0"})
                response.raise_for_status()
                items = response.json().get("message", {}).get("items", [])
            payload = {"source": "crossref", "state": "LIVE", "fetchedAt": datetime.now(timezone.utc).isoformat(), "cacheAgeSeconds": 0,
                       "papers": [self._paper(item) for item in items if isinstance(item, dict)]}
            self._cache[key] = (now, payload)
            return payload
        except Exception as exc:
            if cached:
                return {**cached[1], "state": "STALE", "cacheAgeSeconds": age, "reason": f"Live Crossref refresh failed: {exc}"}
            return {"source": "crossref", "state": "UNAVAILABLE", "reason": str(exc), "papers": []}
