import json
import logging
import httpx
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger("llm_orchestrator")

class LLMOrchestrator:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is missing. LLM capabilities will be restricted.")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

    async def _generate_content(self, prompt: str) -> str:
        """Helper to call Gemini REST API to bypass Python 3.14 protobuf bug."""
        if not self.api_key:
            raise Exception("No API key")
            
        url = f"{self.base_url}?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                raise Exception(f"Unexpected response format: {data}")

    async def resolve_context(self, query: str, history: List[Dict[str, str]] = None) -> str:
        if not self.api_key or not history:
            return query
            
        history_text = "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in history[-4:]])
        
        prompt = f"""
You are an intent resolution engine.
Given the conversation history and a new user query, rewrite the new query to be completely self-contained.
Replace pronouns (it, they, there) with the entities they refer to from the history.
If the query is already self-contained, just return it exactly as is.
DO NOT answer the query. ONLY return the rewritten query string.

History:
{history_text}

New Query: "{query}"

Rewritten Query:"""
        try:
            text = await self._generate_content(prompt)
            return text.strip().strip('"')
        except Exception as e:
            logger.error(f"Context resolution failed: {e}")
            return query
            
    async def resolve_temporal_context(self, query: str) -> Dict[str, Any]:
        """
        Extracts temporal context from the query, falling back to LLM if regex fails.
        Returns a dict matching TemporalContext fields.
        """
        import re
        from datetime import date
        
        # Simple deterministic parsing for "between YYYY and YYYY"
        between_match = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", query, re.IGNORECASE)
        if between_match:
            return {
                "mode": "historical",
                "start_date": f"{between_match.group(1)}-01-01",
                "end_date": f"{between_match.group(2)}-12-31",
                "resolution": "monthly",
                "analysis": ["trend"]
            }
            
        # Deterministic parsing for "last X years"
        last_match = re.search(r"last\s+(\d+)\s+years", query, re.IGNORECASE)
        if last_match:
            years = int(last_match.group(1))
            current_date = date.today()
            return {
                "mode": "historical",
                "start_date": f"{current_date.year - years}-{current_date.month:02d}-{current_date.day:02d}",
                "end_date": current_date.isoformat(),
                "resolution": "monthly",
                "analysis": ["trend"]
            }
            
        # Fallback to LLM
        if not self.api_key:
            return {"mode": "live"}
            
        prompt = f"""
You are a temporal extraction engine.
Analyze the query and determine if the user is asking for historical data.
If it is a live/operational query (e.g. "what is the wave height", "is it safe to fish"), return:
{{"mode": "live"}}

If it is a historical query (e.g. "SST in 2019", "how has it changed"), extract the start and end dates.
Return ONLY valid JSON matching this structure:
{{
    "mode": "historical",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "resolution": "monthly",
    "analysis": ["trend"]
}}

Query: "{query}"
"""
        try:
            text = await self._generate_content(prompt)
            clean_text = text.strip().replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_text)
            return result
        except Exception as e:
            logger.error(f"Temporal extraction failed: {e}")
            return {"mode": "live"}

    async def determine_agents(self, resolved_query: str, agent_registry: Dict[str, Any]) -> List[str]:
        if not self.api_key:
            return list(agent_registry.keys())
            
        registry_descriptions = ""
        for name, agent in agent_registry.items():
            registry_descriptions += f"- {name}: mode_support={agent.spec.mode_support}, dependencies={agent.spec.dependencies}\n"

        prompt = f"""
You are the central intent router for an advanced Marine Intelligence Platform.
Based on the user's query, determine exactly which specialized agents need to be executed.

Available Agents:
{registry_descriptions}

Rules:
1. If the user asks about safety, storms, or IMD colors, include 'weather', 'risk', and 'reporting'.
2. If the user asks about fishing zones (PFZ), SST, or chlorophyll, include 'ocean' and 'geospatial'.
3. If the user asks an academic, analytical, or scientific question (e.g., "Why...", "How does climate change...", "Research on..."), include 'research'.
4. Always include dependencies of the agents you select (e.g. 'risk' requires 'weather', 'ocean', 'geospatial').
5. Return ONLY a valid JSON array of strings representing the agent names. DO NOT wrap in markdown code blocks like ```json.

User Query: "{resolved_query}"
"""
        try:
            text = await self._generate_content(prompt)
            clean_text = text.strip().replace("```json", "").replace("```", "").strip()
            selected_agents = json.loads(clean_text)
            
            if not isinstance(selected_agents, list):
                raise ValueError("LLM did not return a list")
                
            return selected_agents
        except Exception as e:
            logger.error(f"Intent routing failed: {e}. Falling back to default DAG.")
            return ["weather", "ocean", "geospatial", "risk", "reporting", "research"]

    async def synthesize_response(self, query: str, orchestration_results: Dict[str, Any], history: List[Dict[str, str]] = None) -> str:
        if not self.api_key:
            return "I am operating in offline mode. Please refer to the raw data payloads below."
            
        agent_data = orchestration_results.get("agent_results", {})
        
        history_text = ""
        if history:
            history_text = "Conversation History:\n" + "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in history[-4:]])

        prompt = f"""
You are ORCA, an advanced, highly capable Marine Intelligence Conversational Agent.
Your job is to answer the user's query clearly and professionally based ONLY on the provided JSON data.

{history_text}

User Query: "{query}"

System Data (Output from specialized DAG agents):
{json.dumps(agent_data, indent=2, default=str)}

Rules for synthesis:
1. **MULTILINGUAL SUPPORT (CRITICAL):** Automatically detect the language of the 'User Query' (e.g., Hindi, Marathi, Gujarati, English). You MUST respond in that EXACT SAME regional language naturally.
2. Be concise but comprehensive. Provide explainable, evidence-based recommendations based on the System Data.
3. If the user is asking about safety, explicitly mention the BSI score, IMD color code, and any regulatory warnings.
4. **PROVENANCE RULE (CRITICAL):** If historical climate data is present (e.g., from Open-Meteo ERA5-Ocean), explicitly state the dataset provenance as "Source: Open-Meteo, Dataset: ERA5-Ocean, Data type: Reanalysis". NEVER conflate Reanalysis data with "direct satellite observations".
5. **SCIENTIFIC CAUSALITY RULE:** Separate correlation from causation. If a trend coincides with a finding from a research paper, say they coincide or provide possible mechanisms. Do NOT claim the trend definitively caused the finding unless cited explicitly.
6. **CITATION INTEGRITY:** If academic research data is present in the System Data, you MUST attribute claims directly to the provided papers using inline brackets (e.g., [1], [2]). At the bottom of your response, provide a 'References' section formatted as: `[1] Paper Title - Authors - Year - Link/DOI`. Never fabricate citations.
7. Do NOT hallucinate data. If a specific metric or paper is not in the JSON, do not mention it.
8. Use markdown formatting to make the response highly readable.
"""
        try:
            text = await self._generate_content(prompt)
            return text.strip()
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return "An error occurred while synthesizing the response from the marine models."

    async def generate_followups(self, query: str, orchestration_results: Dict[str, Any], history: List[Dict[str, str]] = None) -> List[str]:
        if not self.api_key:
            return []
            
        agent_data = orchestration_results.get("agent_results", {})
        
        history_text = ""
        if history:
            history_text = "Conversation History:\n" + "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in history[-4:]])

        prompt = f"""
You are an assistant suggesting next steps for a user querying a Marine Intelligence Platform.
Based on the conversation history, the current query, and the system data retrieved, suggest between 0 and 3 follow-up questions the user might logically ask next.
If the query was very simple and no follow-ups are necessary, return an empty array [].
If academic research was queried, suggest research-aware follow-ups.

{history_text}

User Query: "{query}"
System Data: {json.dumps(agent_data, indent=2, default=str)}

Return ONLY a valid JSON array of strings containing the follow-up questions.
"""
        try:
            text = await self._generate_content(prompt)
            clean_text = text.strip().replace("```json", "").replace("```", "").strip()
            followups = json.loads(clean_text)
            if not isinstance(followups, list):
                return []
            return followups[:3] # Max 3
        except Exception as e:
            logger.error(f"Follow-up generation failed: {e}")
            return []
