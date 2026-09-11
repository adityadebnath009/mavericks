"""Source-aware, deduplicated literature aggregation for the Console."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable

from app.agents.providers.openalex_research_provider import OpenAlexResearchProvider
from app.agents.providers.crossref_research_provider import CrossrefResearchProvider
from app.agents.providers.europe_pmc_research_provider import EuropePMCResearchProvider


class ResearchLiteratureProvider:
    _marine_terms = ("marine", "ocean", "fisher", "fish", "coastal", "chlorophyll", "sea surface", "seaweed", "pelagic", "oceanograph", "bay of bengal")
    _provider_timeout_seconds = 8.0

    @classmethod
    def _research_query(cls, query: str) -> str:
        """Turn a conversational research question into scholarly terms.

        This is a deterministic retrieval query, not an LLM rewrite.  It
        prevents general-economics papers about "productivity" from outranking
        marine fisheries evidence.
        """
        q = query.lower()
        if any(term in q for term in ("productivity", "decline", "fish", "fisher")):
            terms = ["marine fisheries productivity decline", "chlorophyll", "sea surface temperature"]
            if "visakhapatnam" in q:
                terms.extend(["Visakhapatnam", "Bay of Bengal"])
            elif "bay of bengal" in q:
                terms.append("Bay of Bengal")
            elif "india" in q or "indian" in q:
                terms.append("India")
            return " ".join(terms)
        return " ".join(query.split())[:500]

    @classmethod
    def _is_marine_research(cls, paper: Dict[str, Any]) -> bool:
        title = (paper.get("title") or "").lower()
        return any(term in title for term in cls._marine_terms)

    @staticmethod
    def _key(paper: Dict[str, Any]) -> str:
        doi = (paper.get("doi") or "").lower().replace("https://doi.org/", "")
        if doi:
            return f"doi:{doi}"
        return "title:" + " ".join("".join(char if char.isalnum() else " " for char in (paper.get("title") or "").lower()).split())

    @classmethod
    def _merge(cls, responses: Iterable[Dict[str, Any]], limit: int) -> list[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        for response in responses:
            for paper in response.get("papers", []):
                if not isinstance(paper, dict) or not paper.get("title") or not cls._is_marine_research(paper):
                    continue
                key = cls._key(paper)
                existing = merged.get(key)
                if not existing:
                    merged[key] = {**paper, "sources": list(paper.get("sources") or [response.get("source")])}
                    continue
                existing["sources"] = list(dict.fromkeys([*(existing.get("sources") or []), *(paper.get("sources") or [response.get("source")])]))
                # Preserve the first provider's title/links while filling missing metadata.
                for field in ("doi", "landingPageUrl", "publicationDate", "citationCount", "source", "id"):
                    if existing.get(field) in (None, "") and paper.get(field) not in (None, ""):
                        existing[field] = paper[field]
                existing["isOpenAccess"] = bool(existing.get("isOpenAccess") or paper.get("isOpenAccess"))
        return list(merged.values())[:limit]

    async def search(self, query: str, limit: int = 6) -> Dict[str, Any]:
        scholarly_query = self._research_query(query)
        async def bounded_search(provider: Any, source: str) -> Dict[str, Any]:
            """Let one scholarly API fail without withholding the others."""
            try:
                return await asyncio.wait_for(
                    provider.search(scholarly_query, limit), timeout=self._provider_timeout_seconds
                )
            except TimeoutError:
                return {"source": source, "state": "UNAVAILABLE", "papers": [], "reason": "Research provider timed out."}
            except Exception:
                return {"source": source, "state": "UNAVAILABLE", "papers": [], "reason": "Research provider is unavailable."}
        responses = await asyncio.gather(
            bounded_search(OpenAlexResearchProvider(), "openalex"),
            bounded_search(CrossrefResearchProvider(), "crossref"),
            bounded_search(EuropePMCResearchProvider(), "europe_pmc"),
        )
        papers = self._merge(responses, limit)
        states = {item.get("source"): item.get("state") for item in responses}
        usable = [item for item in responses if item.get("state") in {"LIVE", "CACHED", "STALE"}]
        state = "LIVE" if any(item.get("state") == "LIVE" for item in usable) else ("CACHED" if usable else "UNAVAILABLE")
        return {"source": "research_literature", "state": state, "query": scholarly_query, "papers": papers, "providers": responses, "providerStates": states,
                "reason": None if usable else "No scholarly literature provider is reachable."}
