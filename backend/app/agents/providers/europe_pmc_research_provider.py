"""Europe PMC open-access literature fallback for Intelligence Console only."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import httpx


class EuropePMCResearchProvider:
    _url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    _cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
    _ttl_seconds = 6 * 60 * 60

    @staticmethod
    def _paper(item: Dict[str, Any]) -> Dict[str, Any]:
        doi = item.get("doi")
        source, identifier = item.get("source"), item.get("id")
        record_url = f"https://europepmc.org/article/{source}/{identifier}" if source and identifier else None
        return {
            "id": f"https://doi.org/{doi}" if doi else record_url,
            "title": item.get("title") or "Untitled work",
            "publicationDate": item.get("firstPublicationDate") or item.get("pubYear"),
            "citationCount": item.get("citedByCount"),
            "doi": f"https://doi.org/{doi}" if doi else None,
            "source": item.get("journalTitle") or source,
            "landingPageUrl": item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url") if isinstance(item.get("fullTextUrlList"), dict) and item.get("fullTextUrlList", {}).get("fullTextUrl") else record_url,
            "isOpenAccess": item.get("isOpenAccess") == "Y",
            "sources": ["europe_pmc"],
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
                response = await client.get(self._url, params={"query": key, "format": "json", "resultType": "lite", "pageSize": min(max(limit, 1), 10)})
                response.raise_for_status()
                items = response.json().get("resultList", {}).get("result", [])
            payload = {"source": "europe_pmc", "state": "LIVE", "fetchedAt": datetime.now(timezone.utc).isoformat(), "cacheAgeSeconds": 0,
                       "papers": [self._paper(item) for item in items if isinstance(item, dict)]}
            self._cache[key] = (now, payload)
            return payload
        except Exception as exc:
            if cached:
                return {**cached[1], "state": "STALE", "cacheAgeSeconds": age, "reason": f"Live Europe PMC refresh failed: {exc}"}
            return {"source": "europe_pmc", "state": "UNAVAILABLE", "reason": str(exc), "papers": []}
