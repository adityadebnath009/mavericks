import math
import httpx
import asyncio
import time
import logging
from typing import Dict, Any, List

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.config import settings

logger = logging.getLogger("research_agent")

class AcademicResearchAgent(AbstractAgent):
    """
    Fetches open-access research papers from OpenAlex for deep analytical queries.
    """
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="research",
            dependencies=[], # Independent
            mode_support=["fisheries", "routing"]
        )
        
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """OpenAlex returns abstracts as inverted indexes. We must reconstruct them."""
        if not inverted_index:
            return ""
        try:
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort(key=lambda x: x[0])
            return " ".join([word for pos, word in word_positions])
        except Exception as e:
            logger.error(f"Failed to reconstruct abstract: {e}")
            return ""

    def _rank_works(self, works: List[Dict]) -> List[Dict]:
        """
        Rank papers by a combination of relevance, recency, citation signal, and OA availability.
        """
        scored_works = []
        for w in works:
            year = w.get("publication_year") or 2000
            recency_score = max(0, year - 2000) * 0.1
            
            is_oa = w.get("primary_location", {}).get("is_oa", False) if w.get("primary_location") else False
            oa_score = 1.0 if is_oa else 0.0
            
            citations = w.get("cited_by_count", 0)
            citation_score = min(math.log10(citations + 1), 4.0) * 0.5
            
            has_abstract = bool(w.get("abstract_inverted_index"))
            
            total_score = recency_score + oa_score + citation_score + (2.0 if has_abstract else 0.0)
            scored_works.append((total_score, w))
            
        scored_works.sort(key=lambda x: x[0], reverse=True)
        return [w for score, w in scored_works]

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        
        query = context.query
        if not query:
            return AgentResult(agent_name=self.spec.name, status="skipped", data={}, errors=["No query provided for research."])
            
        safe_query = query.replace('?', '').replace('*', '').replace('"', '')
        
        params = {
            "search": safe_query,
            "per_page": 100,
            "select": "id,doi,title,authorships,publication_year,primary_location,abstract_inverted_index,cited_by_count"
        }
        
        if settings.OPENALEX_API_KEY:
            params["api_key"] = settings.OPENALEX_API_KEY
            
        max_retries = 3
        delay = 1.0
        data = None
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                try:
                    resp = await client.get("https://api.openalex.org/works", params=params, timeout=10.0)
                    if resp.status_code == 429:
                        if attempt == max_retries - 1:
                            raise Exception("Rate limit exceeded")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                        
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        return AgentResult(agent_name=self.spec.name, status="failed", data={}, errors=[str(e)])
                    await asyncio.sleep(delay)
                    delay *= 2
                    
        if not data or "results" not in data:
            return AgentResult(agent_name=self.spec.name, status="failed", data={}, errors=["Invalid response from OpenAlex"])
            
        ranked_works = self._rank_works(data["results"])
        top_works = ranked_works[:5]
        
        evidence_list = []
        for w in top_works:
            authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:3]]
            author_str = ", ".join(filter(None, authors))
            if len(w.get("authorships", [])) > 3:
                author_str += " et al."
                
            abstract = self._reconstruct_abstract(w.get("abstract_inverted_index", {}))
            primary_loc = w.get("primary_location", {}) or {}
            
            evidence_list.append({
                "id": w.get("id"),
                "doi": w.get("doi") or primary_loc.get("pdf_url") or "",
                "title": w.get("title", "Untitled"),
                "authors": author_str,
                "year": w.get("publication_year", "Unknown"),
                "citations": w.get("cited_by_count", 0),
                "abstract": abstract if abstract else None, # explicitly None if unavailable
                "is_oa": primary_loc.get("is_oa", False)
            })
            
        latency = (time.perf_counter() - start_time) * 1000
        
        return AgentResult(
            agent_name=self.spec.name,
            status="success",
            data={"evidence": evidence_list, "total_found": data.get("meta", {}).get("count", 0)},
            latency_ms=round(latency, 2),
            sources=["OpenAlex API"]
        )
