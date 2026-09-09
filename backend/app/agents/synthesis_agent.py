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
            dependencies=["weather", "ocean", "risk", "reporting", "geospatial", "safety_evidence"],
            mode_support=["fisheries", "routing", "research"]
        )

    def _generate_briefing(self, context: AgentContext, risk_data: dict, reporting_data: dict, weather_data: dict, ocean_data: dict) -> dict:
        """Calls Gemini to write the executive summary and extract hazards."""
        if not GEMINI_API_KEY:
            return self._grounded_fallback(context, risk_data, weather_data, ocean_data)
            
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
                **self._grounded_fallback(context, risk_data, weather_data, ocean_data),
                "synthesis_notice": "The LLM synthesis provider was unavailable; this briefing was generated from the completed agent evidence."
            }

    @staticmethod
    def _grounded_fallback(context: AgentContext, risk_data: dict, weather_data: dict, ocean_data: dict) -> dict:
        """Evidence-only briefing used when an optional LLM provider is unavailable."""
        assessment = str(risk_data.get("final_fused_risk", "UNKNOWN")).upper()
        wind = weather_data.get("max_wind_speed")
        wave = ocean_data.get("wave_height", ocean_data.get("base_wave_height"))
        sst = ocean_data.get("sst")
        # The shared GEE helper returns NOAA OISST's stored value.  Normalize it
        # only for the Intelligence Console narrative; legacy PFZ endpoints keep
        # their existing behaviour and contracts untouched.
        if isinstance(sst, (int, float)) and abs(sst) > 100:
            sst = sst * 0.01
        chlorophyll = ocean_data.get("chlorophyll")
        location = f"{context.latitude:.3f}, {context.longitude:.3f}"
        facts = []
        if wind is not None:
            facts.append(f"wind up to {float(wind):.0f} km/h")
        if wave is not None:
            facts.append(f"waves about {float(wave):.1f} m")
        marine_facts = []
        if sst is not None:
            marine_facts.append(f"SST {float(sst):.1f}°C")
        if chlorophyll is not None:
            marine_facts.append(f"chlorophyll {float(chlorophyll):.2f} mg/m³")
        condition_text = ", ".join(facts) if facts else "available marine observations"
        productivity_text = ", ".join(marine_facts) if marine_facts else "ocean productivity evidence"
        hazards = []
        for alert in weather_data.get("timeline_alerts", [])[:3]:
            if isinstance(alert, dict) and alert.get("message"):
                hazards.append({"text": alert["message"], "severity": alert.get("severity", assessment)})
        if not hazards:
            hazards.append({"text": f"Computed marine risk is {assessment} based on {condition_text}.", "severity": assessment})
        is_pfz = ocean_data.get("is_pfz") is True
        summary = (
            f"At {location}, ORCA assessed the requested operating point as {assessment}. "
            f"The completed weather and ocean agents report {condition_text}; {productivity_text}. "
            + ("The point meets the configured local PFZ suitability rule." if is_pfz else "The point does not meet the configured local PFZ suitability rule.")
        )
        if assessment in {"HIGH", "EXTREME", "UNSAFE"}:
            directive = "This is not a confirmed safe operating window. Delay departure or choose a lower-risk window; review the listed hazards before proceeding."
        elif assessment == "MODERATE":
            directive = "This is not a confirmed safe operating window. Proceed only with a conservative vessel plan and monitor live weather updates."
        else:
            directive = "Continue to monitor live weather and geofence updates during the operation."
        return {
            "executive_summary": summary,
            "identified_hazards": hazards,
            "operational_directives": [{"text": directive}],
            "followups": ["What is the primary risk factor here?", "Show the local PFZ suitability evidence.", "What data is cached versus live?"]
        }

    @staticmethod
    def _safety_briefing(context: AgentContext, safety_data: dict) -> dict:
        """Safety-first narrative. Fisheries signals are intentionally excluded."""
        assessment = safety_data.get("assessment", "PARTIAL")
        certification = safety_data.get("certification", "PARTIAL")
        weather = safety_data.get("weather", {})
        marine = safety_data.get("marine", {})
        bsi_score = safety_data.get("bsi", {}).get("severityScore")
        facts = []
        if weather.get("windSpeedKmh") is not None:
            facts.append(f"wind {weather['windSpeedKmh']:.0f} km/h")
        if weather.get("windGustKmh") is not None:
            facts.append(f"gusts {weather['windGustKmh']:.0f} km/h")
        if marine.get("waveHeightM") is not None:
            facts.append(f"significant waves {marine['waveHeightM']:.1f} m")
        if marine.get("swellHeightM") is not None:
            facts.append(f"swell {marine['swellHeightM']:.1f} m")
        if marine.get("currentSpeedMs") is not None:
            facts.append(f"currents {marine['currentSpeedMs']:.1f} m/s")
        evidence_text = ", ".join(facts) or "critical marine observations are unavailable"
        hazards = safety_data.get("hazards", [])
        if not hazards:
            hazards = ["No threshold breach was found in the available safety evidence."]
        if assessment == "SAFE" and certification == "VALID":
            directive = "The available weather and marine evidence meets the configured ORCA safety criteria; continue monitoring during the operation."
        elif assessment == "CAUTION":
            directive = "This is not a confirmed safe operating window. Use a conservative vessel plan and reassess before departure."
        elif assessment == "UNSAFE":
            directive = "Do not depart in this operating window. Wait for a lower-risk forecast and reassess all marine conditions."
        else:
            directive = "Safety cannot be certified because a critical weather or marine source is unavailable; do not treat this as a go decision."
        summary = (
            f"Safety verdict for {context.latitude:.3f}, {context.longitude:.3f}: {assessment} ({certification}). "
            f"ORCA Boat Safety Index severity is {bsi_score if bsi_score is not None else 'unavailable'}/100; available evidence reports {evidence_text}."
        )
        return {
            "executive_summary": summary,
            "identified_hazards": [{"text": hazard, "severity": assessment} for hazard in hazards],
            "operational_directives": [{"text": directive}],
            "followups": ["Show the Boat Safety Index evidence.", "Which weather or sea-state input is driving risk?", "What source data is unavailable?"]
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

        safety_res = pr.get("safety_evidence", {})
        if isinstance(safety_res, AgentResult):
            safety_res = safety_res.data

        # Planner serializes AgentResult instances into {data, status, ...}; unwrap
        # those records before mapping them into the public V2 contract.
        risk_res = risk_res.get("data", risk_res) if isinstance(risk_res, dict) else risk_res
        weather_res = weather_res.get("data", weather_res) if isinstance(weather_res, dict) else weather_res
        reporting_res = reporting_res.get("data", reporting_res) if isinstance(reporting_res, dict) else reporting_res
        geospatial_res = geospatial_res.get("data", geospatial_res) if isinstance(geospatial_res, dict) else geospatial_res
        safety_res = safety_res.get("data", safety_res) if isinstance(safety_res, dict) else safety_res

        # 1. Map Core Fields
        safety_query = any(term in (context.query or "").lower() for term in ("safe", "safety", "hazard", "venture", "weather", "storm", "cyclone", "lightning"))
        assessment = safety_res.get("assessment", "PARTIAL") if safety_query else risk_res.get("final_fused_risk", "UNKNOWN").upper()
        certification = safety_res.get("certification", "PARTIAL") if safety_query else ("VALID" if "weather" in pr and "ocean" in pr else "UNVALIDATED")
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
        
        ocean_res = pr.get("ocean", {})
        ocean_res = ocean_res.get("data", ocean_res) if isinstance(ocean_res, dict) else ocean_res

        # 3. Call Gemini, or produce an evidence-only briefing if the optional
        # provider is unavailable.
        llm_output = self._safety_briefing(context, safety_res) if safety_query else self._generate_briefing(context, risk_res, reporting_res, weather_res, ocean_res)
        
        
        # Check GEE Service status dynamically for frontend UI
        # 4. MapData

        mapData = {
            # The chat API has no destination contract, so never present the
            # geospatial agent's demonstration route as a real recommended route.
            "activeRoute": None,
            "pfzPoints": ([{
                "lat": context.latitude,
                "lon": context.longitude,
                "properties": {
                    "kind": "local_suitability_observation",
                    "pfzScore": ocean_res.get("pfz_score"),
                    "scope": ocean_res.get("pfz_observation_scope", "requested_point")
                }
            }] if ocean_res.get("is_pfz") else []),
            "geofences": geospatial_res.get("geofences", []),
            "overlayLayers": GEEService.build_overlay_layers(),
            "safetyEvidence": safety_res if safety_query else None,
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
