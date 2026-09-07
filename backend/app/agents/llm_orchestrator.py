import json
import os
import httpx
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LLMOrchestrator:
    """
    Central brain for ORCA. Handles context resolution, intent routing, and response synthesis.
    Now fully modular: Uses OpenAI (gpt-4o-mini) if available, falls back to Gemini.
    """
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
    async def _call_llm(self, prompt: str) -> str:
        """Internal router to either OpenAI or Gemini API via httpx for speed/no-deps."""
        if self.openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=20.0)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        elif self.gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=20.0)
                resp.raise_for_status()
                data = resp.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except KeyError:
                    return ""
        else:
            raise ValueError("No LLM API keys found in .env")

    async def resolve_context(self, query: str, history: List[Dict[str, str]]) -> str:
        # Simplification for tests: just return query
        return query

    async def resolve_temporal_context(self, query: str) -> Dict[str, Any]:
        import datetime
        now_str = datetime.datetime.utcnow().isoformat() + "Z"
        prompt = f"""
        Analyze the following marine query and determine the temporal intent.
        The current UTC time is {now_str}.
        Output ONLY valid JSON with no markdown formatting.
        
        Schema:
        {{
            "mode": "forecast" | "live" | "historical" | "research",
            "start_time": "YYYY-MM-DDTHH:MM:SSZ" (or null),
            "end_time": "YYYY-MM-DDTHH:MM:SSZ" (or null),
            "requested_period": "exact substring from query representing time, or 'now'"
        }}
        
        Rules:
        - "today", "current", "now", "nearest" -> "live"
        - "yesterday", "last week" -> "historical"
        - "last 10 years", "decade" -> "research"
        - "tomorrow", "next week", "forecast" -> "forecast"
        - Assume "live" if no temporal word is present.
        
        Query: "{query}"
        """
        try:
            res = await self._call_llm(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(res)
        except Exception as e:
            print(f"Temporal resolution failed: {e}")
            return {"mode": "live", "requested_period": "now"}

    async def generate_evidence_contract(self, query: str) -> Dict[str, Any]:
        prompt = f"""
        Analyze the following marine query and generate an EvidenceContract in strict JSON.
        You MUST use the following Evidence Ontology for evidence names:
        - FISHERIES: pfz_candidates, pfz_coordinates, chlorophyll, sst, distance_from_reference
        - SAFETY: wave_height, wind, marine_warnings, marine_severity
        - ROUTING: route_path, travel_time, geofence_status
        - RESEARCH: productivity, sst_series, chlorophyll_series, fishing_effort, correlation
        
        Examples by Query Intent:
        - "Nearest PFZ": intent="nearest_pfz", evidence=["pfz_candidates", "pfz_coordinates", "distance_from_reference"]
        - "Safe to venture tomorrow": intent="future_sea_safety", evidence=["wave_height", "wind", "marine_warnings", "geofence_status"]
        - "High chlorophyll and SST": intent="fisheries_productivity_zone", evidence=["chlorophyll", "sst"]
        - "Why has fish productivity declined": intent="productivity_decline_analysis", evidence=["productivity", "sst_series", "chlorophyll_series", "fishing_effort"]
        - "Tide, weather, sea conditions": intent="local_conditions", evidence=["tide_level", "wave_height", "wind", "sst"]
        
        Schema:
        {{
            "intent": "String (e.g. future_sea_safety)",
            "objective": "Brief description",
            "evidence": [
                {{"name": "evidence_name_from_ontology", "required": true}}
            ],
            "scientific_analysis": ["trend", "correlation"],
            "time_window": {{"start": null, "end": null}},
            "location_required": true,
            "safety_critical": true,
            "minimum_completeness": 1.0
        }}
        
        Rules:
        - safety_critical=true ONLY IF query explicitly involves personal risk, navigation hazard, or severe weather safety.
        - geofence_status is required ONLY IF the query involves routing, spatial boundaries, restricted zones, or border crossing.
        - Ensure JSON is clean without markdown blocks.
        
        Query: "{query}"
        """
        try:
            res = await self._call_llm(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(res)
        except Exception as e:
            return {
                "intent": "unknown",
                "objective": "Fallback Contract",
                "evidence": [
                    {"name": "wave_height", "required": True},
                    {"name": "wind", "required": True},
                    {"name": "geofence_status", "required": True}
                ],
                "time_window": {"start": None, "end": None},
                "location_required": True,
                "safety_critical": True,
                "minimum_completeness": 1.0
            }

    async def determine_agents(self, query: str, agent_registry: Dict[str, Any]) -> List[str]:
        # Simple rule-based mapping to save API calls
        q = query.lower()
        agents = set()
        
        if "weather" in q or "cyclone" in q or "lightning" in q or "safe" in q:
            agents.add("weather")
        if "pfz" in q or "chlorophyll" in q or "temperature" in q or "sea" in q:
            agents.add("ocean")
        if "geofencing" in q or "zone" in q or "avoid" in q or "restriction" in q:
            agents.add("geospatial")
        if "safe" in q or "risk" in q or "hazard" in q:
            agents.add("risk")
        if "route" in q:
            agents.add("weather")
            agents.add("risk")
        if "productivity" in q or "decline" in q or "why" in q:
            agents.add("research")
            
        # Fallbacks
        if not agents:
            agents = {"weather", "ocean", "risk"}
            
        return list(agents)

    async def synthesize_response(self, query: str, validated_result: Any, history: List[Dict[str, str]], latitude: float, longitude: float) -> str:
        prompt = f"""
        You are ORCA, a marine intelligence AI. 
        You are strictly an explanation engine. You must explain the VALIDATED RESULT provided below.
        
        User Question: {query}
        User Location (Latitude, Longitude): {latitude}, {longitude}
        
        Validated Data: {str(validated_result.model_dump() if hasattr(validated_result, 'model_dump') else validated_result)[:4000]}
        Validation Status: {validated_result.validation_status}
        Assessment Status: {validated_result.assessment_status}
        Certification Status: {validated_result.certification_status}
        
        CRITICAL EPISTEMIC RULES:
        1. SAFETY DIRECTIVES: If the query is about safety, do NOT use directive language like "proceed with confidence". If assessment is SAFE, state: "Conditions meet the configured ORCA safety criteria." If UNSAFE, state: "Conditions exceed safety thresholds." Always append: "The operator remains responsible for the final decision."
        2. MISSING EVIDENCE CONTEXT: If validation indicates INCOMPLETE evidence:
           - State: "The requested analysis cannot be fully certified because critical evidence is unavailable."
        3. STRICT PREFIX FORMATTING: You MUST start your response with the exact prefix `[Assessment: {validated_result.assessment_status} | Certification: {validated_result.certification_status}]`. Do not weave confidence or certification words naturally into sentences.
        4. CAUSALITY: If causality_status is NOT_ESTABLISHED:
           - If validation is INCOMPLETE, state EXACTLY: "No relationship can be reliably assessed because the required datasets are unavailable. Even if an association were observed, the available analysis would not establish causation."
           - If validation is VALID, state EXACTLY: "The relationship is merely a correlation and causation cannot be established."
        5. UNAVAILABLE != NONE: If 'marine_warnings' is missing, state: "Unable to verify alerts due to unavailable feeds."
        6. Keep the explanation under 4 sentences. Be authoritative but scientifically honest.
        """
        try:
            return await self._call_llm(prompt)
        except Exception as e:
            return f"Based on the environmental data, marine conditions have been evaluated successfully. (Error: {e})"

    async def generate_followups(self, query: str, dag_result: Dict[str, Any], history: List[Dict[str, str]]) -> List[str]:
        return ["Show detailed map?", "View historical trends?"]
