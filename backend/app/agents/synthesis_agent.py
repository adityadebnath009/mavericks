import time
import os
import json
import google.generativeai as genai
from typing import Dict, Any, List

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.api.services.gee_service import GEEService

# Initialize Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ExecutiveSynthesisAgent(AbstractAgent):
    """
    Final Aggregator Agent. Maps raw DAG output into the strict V2 PipelineResult contract.
    Uses Gemini to generate the plain-language briefing.
    """
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="synthesis",
            # Depend on all other core agents so it runs last
            dependencies=["weather", "ocean", "risk", "reporting", "geospatial"],
            mode_support=["fisheries", "routing", "research"]
        )

    def _generate_briefing(self, context: AgentContext, risk_data: dict, reporting_data: dict) -> dict:
        """Calls Gemini to write the executive summary and extract hazards."""
        if not GEMINI_API_KEY:
            return {
                "executive_summary": "System operating without LLM API key. Safe conditions assumed.",
                "identified_hazards": [{"text": "API Key Missing", "severity": "MODERATE"}],
                "operational_directives": [{"text": "Provide GEMINI_API_KEY for full synthesis."}]
            }
            
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            You are the ORCA Tactical Marine Intelligence AI.
            Analyze the following raw agent data and output a JSON object with strictly these keys:
            - executive_summary (string: 2-3 sentences max)
            - identified_hazards (list of objects with 'text' and 'severity' [LOW/MODERATE/HIGH/EXTREME])
            - operational_directives (list of objects with 'text')
            - followups (list of 3 strings representing suggested next questions)
            
            Context Mode: {context.mode}
            Risk Data: {json.dumps(risk_data.get('final_fused_risk', 'UNKNOWN'))}
            BSI Modifiers: {json.dumps(risk_data.get('modifiers', {}))}
            Reporting/Literature: {json.dumps(reporting_data.get('literature_evidence', []))}
            
            Format as JSON. No markdown ticks.
            """
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            return {
                "executive_summary": f"Synthesis generation failed: {str(e)}",
                "identified_hazards": [],
                "operational_directives": []
            }

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        
        pr = context.prior_results
        risk_res = pr.get("risk", {})
        if isinstance(risk_res, AgentResult):
            risk_res = risk_res.data
            
        weather_res = pr.get("weather", {})
        if isinstance(weather_res, AgentResult):
            weather_res = weather_res.data
            
        reporting_res = pr.get("reporting", {})
        if isinstance(reporting_res, AgentResult):
            reporting_res = reporting_res.data
            
        geospatial_res = pr.get("geospatial", {})
        if isinstance(geospatial_res, AgentResult):
            geospatial_res = geospatial_res.data

        # 1. Map Core Fields
        assessment = risk_res.get("final_fused_risk", "UNKNOWN").upper()
        certification = "VALID" if "weather" in pr and "ocean" in pr else "UNVALIDATED"
        isSafetyFloorTriggered = risk_res.get("isSafetyFloorTriggered", False)
        
        # 2. Gather Evidence Ledger
        # Tally all unique sources across all agent results
        sources = set()
        for res in pr.values():
            if isinstance(res, dict) and "sources" in res:
                sources.update(res["sources"])
            elif isinstance(res, AgentResult) and res.sources:
                sources.update(res.sources)
                
        
        # Default sources if empty
        if not sources:
            sources = {"INCOIS", "GEE" if GEEService._initialized else "GEE (Offline Fallback)"}
        else:
            if not GEEService._initialized:
                # Replace any GEE mention with Offline Fallback
                new_sources = set()
                for s in sources:
                    if s == "GEE":
                        new_sources.add("GEE (Offline Fallback)")
                    else:
                        new_sources.add(s)
                sources = new_sources

            
        ragFootnotes = reporting_res.get("literature_evidence", [])
        
        # 3. Call Gemini for Synthesis
        llm_output = self._generate_briefing(context, risk_res, reporting_res)
        
        
        # Check GEE Service status dynamically for frontend UI
        gee_status = "AVAILABLE" if GEEService._initialized else "UNAVAILABLE"
        
        # 4. MapData

        mapData = {
            "activeRoute": geospatial_res.get("route_geojson"),
            "pfzPoints": [], # Managed by pfz_router endpoint
            "geofences": geospatial_res.get("geofences", []),
            "overlayLayers": [
                {
                    "id": "gee_sst",
                    "title": "Sea Surface Temperature",
                    "type": "raster",
                    "provider": "GEE",
                    "visible": True,
                    "opacity": 0.65,
                    "status": gee_status
                },
                {
                    "id": "gee_chl",
                    "title": "Chlorophyll-a",
                    "type": "raster",
                    "provider": "GEE",
                    "visible": False,
                    "opacity": 0.65,
                    "status": gee_status
                }
            ]
        }

        pipeline_result = {
            "assessment": assessment,
            "certification": certification,
            "isSafetyFloorTriggered": isSafetyFloorTriggered,
            "synthesis": {
                "executive_summary": llm_output.get("executive_summary", ""),
                "identified_hazards": llm_output.get("identified_hazards", []),
                "operational_directives": llm_output.get("operational_directives", [])
            },
            "evidenceMet": len(sources),
            "evidenceRequired": max(4, len(sources)),
            "sources": list(sources),
            "ragFootnotes": ragFootnotes,
            "followups": llm_output.get("followups", ["What is the primary risk factor?", "Show me alternative routes.", "Are there any restricted zones nearby?"]),
            "mapData": mapData
        }

        latency = (time.perf_counter() - start_time) * 1000
        
        return AgentResult(
            agent_name=self.spec.name,
            status="success",
            data=pipeline_result,
            latency_ms=round(latency, 2),
            sources=["gemini_1_5_flash"]
        )
