"""Safety-only final agent for the Intelligence Console.

It deliberately has no fisheries or research dependencies.  This prevents SST,
chlorophyll and generic literature from obscuring a boat-safety response.
"""
from __future__ import annotations

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.agents.intelligence_intent_policy import classify_intent


class SafetySynthesisAgent(AbstractAgent):
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(name="safety_synthesis", dependencies=["safety_evidence", "geospatial"], mode_support=["fisheries", "routing", "weather"])

    async def analyze(self, context: AgentContext) -> AgentResult:
        prior = context.prior_results
        safety = prior.get("safety_evidence", {}).get("data", prior.get("safety_evidence", {}))
        geo = prior.get("geospatial", {}).get("data", prior.get("geospatial", {}))
        assessment = safety.get("assessment", "PARTIAL")
        certification = safety.get("certification", "PARTIAL")
        weather, marine = safety.get("weather", {}), safety.get("marine", {})
        bsi = safety.get("bsi", {})
        ml_risk = safety.get("mlRisk", {})
        map_evidence = safety.get("mapEvidence", {})
        facts = []
        for label, value, unit in (
            ("wind", weather.get("windSpeedKmh"), "km/h"),
            ("gusts", weather.get("windGustKmh"), "km/h"),
            ("significant waves", marine.get("waveHeightM"), "m"),
            ("swell", marine.get("swellHeightM"), "m"),
            ("wind waves", marine.get("windWaveHeightM"), "m"),
            ("currents", marine.get("currentSpeedMs"), "m/s"),
        ):
            if value is not None:
                facts.append(f"{label} {float(value):.1f} {unit}")
        bsi_score = bsi.get("severityScore")
        bsi_text = f"{float(bsi_score):.1f}/100" if bsi_score is not None else "unavailable"
        summary = (
            f"Safety verdict: {assessment} — {certification}. "
            f"ORCA Boat Safety Index is {bsi_text}. "
            f"ML risk is {ml_risk.get('ml_risk_class', 'unavailable')} ({ml_risk.get('model_status', 'unavailable')}). "
            f"Safety evidence: {', '.join(facts) if facts else 'critical marine data unavailable'}. "
            "Official IMD warning verification is unavailable."
        )
        # Use the Console's one intent policy rather than overlapping words in
        # a query.  For example, “zones to avoid due to hazardous conditions”
        # is a safety request, not a generic conditions briefing.
        intent = classify_intent(context.query).name
        conditions_query = intent == "conditions"
        alerts_query = intent == "alerts"
        model_evidence_available = any(
            source.get("state") in {"LIVE", "CACHED", "STALE"}
            for source in (weather, marine)
        )
        if conditions_query:
            condition_facts = []
            for label, value, unit in (
                ("wind", weather.get("windSpeedKmh"), "km/h"),
                ("gusts", weather.get("windGustKmh"), "km/h"),
                ("visibility", weather.get("visibilityM"), "m"),
                ("rain probability", weather.get("precipitationProbability"), "%"),
                ("significant waves", marine.get("waveHeightM"), "m"),
                ("wind waves", marine.get("windWaveHeightM"), "m"),
                ("swell", marine.get("swellHeightM"), "m"),
                ("current", marine.get("currentSpeedMs"), "m/s"),
                ("sea-surface temperature", marine.get("seaSurfaceTemperatureC"), "°C"),
                ("model sea-level height", marine.get("seaLevelHeightMslM"), "m MSL"),
            ):
                if value is not None:
                    condition_facts.append(f"{label} {float(value):.1f} {unit}")
            summary = (
                f"Local conditions briefing: {', '.join(condition_facts) if condition_facts else 'operational model evidence is unavailable'}. "
                "Open-Meteo supplies modeled wind, waves, currents, and sea level; it is not a local tide-gauge or official IMD warning feed. "
                f"Operational safety status remains {assessment} with certification {certification} because official IMD warning verification is unavailable."
            )
        elif alerts_query:
            modeled_alerts = []
            if (weather.get("windGustKmh") or 0) >= 40:
                modeled_alerts.append(f"gusts up to {float(weather['windGustKmh']):.1f} km/h")
            if (weather.get("precipitationProbability") or 0) >= 70:
                modeled_alerts.append(f"precipitation probability {float(weather['precipitationProbability']):.0f}%")
            if (marine.get("waveHeightM") or 0) >= 2:
                modeled_alerts.append(f"significant waves {float(marine['waveHeightM']):.1f} m")
            if not model_evidence_available:
                summary = (
                    "Open-Meteo modeled hazard evidence is unavailable, so no model-based lightning, cyclone, or marine-alert conclusion can be made. "
                    "Official IMD warning verification is unavailable, so alert clearance cannot be confirmed."
                )
            else:
                summary = (
                    f"Open-Meteo modeled hazard indicators: {', '.join(modeled_alerts) if modeled_alerts else 'no configured threshold breach in the available model fields'}. "
                    "This is model evidence, not an official warning. Official IMD warning verification is unavailable, so alert clearance cannot be confirmed."
                )
        if alerts_query:
            directive = "Treat any modeled threshold breach as an operational warning and verify official IMD/costal authority alerts before departure."
        elif conditions_query:
            directive = "Use these modeled conditions as planning context; verify local tide, harbour, and official-warning information before departure."
        elif assessment == "SAFE" and certification == "VALID":
            directive = "The available forecast meets configured ORCA safety criteria. Continue monitoring before and during departure."
        elif assessment == "UNSAFE":
            directive = "Do not depart in this window. Wait for lower wind/wave conditions and reassess."
        elif assessment == "CAUTION":
            directive = "Not a confirmed safe operating window. Use a conservative vessel plan and reassess immediately before departure."
        else:
            directive = "Safety is not certified because critical marine evidence is unavailable. Do not use this as a go decision."
        hazards = safety.get("hazards") or (["No threshold breach found in the available safety evidence."]
                                             if model_evidence_available else
                                             ["Critical weather and marine hazard evidence is unavailable."])
        map_data = {
            "activeRoute": None,
            "pfzPoints": [],
            "geofences": geo.get("geojson", {"type": "FeatureCollection", "features": []}),
            "overlayLayers": [],
            "bsiGrid": map_evidence.get("bsiGrid"),
            "windVectors": map_evidence.get("windVectors"),
            "currentVectors": map_evidence.get("currentVectors"),
            "safetyMapState": {key: value for key, value in map_evidence.items() if key in {"source", "state", "fetchedAt", "reason", "unavailableCells"}},
            "safetyEvidence": safety,
            "disabledLayers": [{"id": "imd-warning", "title": "Official IMD warnings", "status": "UNAVAILABLE", "unavailableReason": "IMD access and IP whitelisting are pending."}],
        }
        return AgentResult(
            agent_name=self.spec.name,
            status="success",
            data={
                "assessment": assessment,
                "certification": certification,
                "isSafetyFloorTriggered": bool(bsi.get("report", {}).get("isSafetyFloorTriggered", False)),
                "synthesis": {
                    "executive_summary": summary,
                    "identified_hazards": [{"text": item, "severity": assessment} for item in hazards],
                    "operational_directives": [{"text": directive}],
                },
                # IMD verification is a required safety gate.  It deliberately
                # remains unmet until institutional access is provisioned, so
                # a fully populated model forecast is never shown as 100%.
                "evidenceMet": sum(value is not None for value in (weather.get("windSpeedKmh"), weather.get("windGustKmh"), weather.get("visibilityM"), marine.get("waveHeightM"), marine.get("wavePeriodS"), marine.get("swellHeightM"), marine.get("currentSpeedMs"))),
                "evidenceRequired": 8,
                "sources": [weather.get("source", "open_meteo_weather"), marine.get("source", "open_meteo_marine"), "orca_bsi_engine", "xgboost_ml_model"],
                "ragFootnotes": [],
                "followups": ["Show Boat Safety Index evidence.", "Which source is unavailable?", "What is the next lower-risk time window?"],
                "mapData": map_data,
            },
            sources=[weather.get("source", "open_meteo_weather"), marine.get("source", "open_meteo_marine"), "orca_bsi_engine", "xgboost_ml_model"],
        )
