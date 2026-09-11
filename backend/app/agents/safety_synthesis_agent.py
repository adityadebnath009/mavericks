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

    @staticmethod
    def _decision_explanation(safety: dict, geo: dict) -> dict:
        """Turn existing BSI/ML evidence into a traceable, human-readable rationale.

        This is a presentation layer only: values, thresholds, and BSI physics
        are taken directly from the existing deterministic engine output.
        """
        weather, marine = safety.get("weather", {}), safety.get("marine", {})
        bsi, ml = safety.get("bsi", {}), safety.get("mlRisk", {})
        report = bsi.get("report", {}) if isinstance(bsi, dict) else {}
        score = bsi.get("severityScore") if isinstance(bsi, dict) else None
        deterministic = report.get("deterministic_class", "UNKNOWN")
        ml_class = ml.get("ml_risk_class", "UNKNOWN")
        drivers = []

        if score is None:
            drivers.append({"kind": "LIMIT", "label": "ORCA Boat Safety Index", "observation": "Withheld", "meaning": "Critical weather or marine evidence is missing.", "effect": "Cannot support a certified safety decision."})
        else:
            boundary = 85 if score >= 85 else (60 if score >= 60 else (35 if score >= 35 else None))
            meaning = f"Above the configured {boundary}/100 safety boundary." if boundary else "Below the configured caution boundary of 35/100."
            drivers.append({"kind": "DECISION", "label": "Deterministic ORCA BSI", "observation": f"{float(score):.0f}/100 ({deterministic})", "meaning": meaning, "effect": "Sets the deterministic minimum risk level."})

        if safety.get("mlEvidence", {}).get("state") == "LIVE":
            agreement = "agrees with" if ml_class == deterministic else "is evaluated alongside"
            drivers.append({"kind": "MODEL", "label": "XGBoost risk model", "observation": ml_class, "meaning": f"The trained model {agreement} the deterministic assessment.", "effect": "Independent model evidence; it cannot override a higher deterministic safety floor."})
        else:
            drivers.append({"kind": "LIMIT", "label": "XGBoost risk model", "observation": "Unavailable", "meaning": safety.get("mlEvidence", {}).get("reason", "The ML model did not return a live result."), "effect": "No ML conclusion is claimed."})

        threshold_factors = (
            ("Wind gusts", weather.get("windGustKmh"), 40, "km/h", "can affect vessel handling"),
            ("Significant waves", marine.get("waveHeightM"), 2, "m", "increase sea-state risk"),
            ("Swell", marine.get("swellHeightM"), 2, "m", "can increase vessel motion"),
            ("Ocean current", marine.get("currentSpeedMs"), 1.5, "m/s", "can affect vessel control and fuel use"),
            ("Precipitation probability", weather.get("precipitationProbability"), 70, "%", "can reduce visibility and indicate changing conditions"),
        )
        for label, value, threshold, unit, meaning in threshold_factors:
            if value is None:
                continue
            active = float(value) >= threshold
            drivers.append({"kind": "HAZARD" if active else "CONTEXT", "label": label, "observation": f"{float(value):.1f} {unit}", "meaning": f"{meaning.capitalize()}. {'This reaches the configured operational trigger.' if active else f'This is below the configured {threshold:g} {unit} trigger.'}", "effect": "Raises operational caution." if active else "Does not independently trigger the configured hazard rule."})

        physics = []
        hazards = report.get("hazards", {}) if isinstance(report, dict) else {}
        steepness = hazards.get("wave_steepness", {})
        if steepness:
            mu = steepness.get("mu_s")
            physics.append({"label": "Wave steepness", "observation": f"μ={mu}" if mu is not None else "Unavailable", "meaning": "Wave height and period are converted into a physics-based steepness measure.", "effect": "BSI trigger active." if steepness.get("triggered") else "Not a BSI trigger at the configured 0.04 threshold."})
        crossing = hazards.get("crossing_sea", {})
        if crossing:
            physics.append({"label": "Crossing seas", "observation": "Unavailable" if not crossing.get("available") else f"severity {crossing.get('severity', 0):.2f}", "meaning": crossing.get("reason", "Wind-wave and swell directions are assessed for crossing-sea energy."), "effect": "BSI trigger active." if crossing.get("triggered") else "Does not add a crossing-sea trigger."})
        rapid = hazards.get("rapid_development", {})
        if rapid:
            physics.append({"label": "Rapid wave development", "observation": f"{float(rapid.get('relative_change', 0)) * 100:.0f}% change", "meaning": "Compares available wave history with the current wave height.", "effect": "BSI trigger active." if rapid.get("triggered") else "No rapid-development trigger in available history."})

        safeguards = [{"label": "Official IMD warning", "state": safety.get("officialWarning", {}).get("state", "UNAVAILABLE"), "meaning": safety.get("officialWarning", {}).get("reason", "Official warning verification is unavailable."), "effect": "Certification remains PARTIAL; this is not an official alert clearance."}]
        if geo:
            safeguards.append({"label": "Geofence", "state": geo.get("status", "UNKNOWN"), "meaning": geo.get("message", "Geofence result is shown on the map and evidence ledger."), "effect": "Restrictions are evaluated separately from weather and BSI."})
        return {"version": "orca-explainability-v1", "decision": safety.get("assessment", "PARTIAL"), "drivers": drivers, "physics": physics, "safeguards": safeguards}

    @staticmethod
    def _fisherman_advisory(safety: dict, geo: dict) -> dict:
        """Plain-language, action-first guidance derived from the live verdict.

        This deliberately does not re-score conditions or invent a local
        authority instruction. It translates the existing assessment, hazards,
        and evidence limitations into short operational guidance.
        """
        assessment = safety.get("assessment", "PARTIAL")
        score = (safety.get("bsi") or {}).get("severityScore")
        weather, marine = safety.get("weather", {}), safety.get("marine", {})
        reasons, actions = [], []
        if assessment == "UNSAFE":
            headline = "Do not leave for sea in this weather window."
            actions.append("Wait for calmer conditions, then ask for a new safety check before departure.")
        elif assessment == "CAUTION":
            headline = "Wait and check again just before leaving; this is not a confirmed safe window."
            actions.append("If you must operate, use a conservative vessel plan and keep a safe return margin.")
        elif assessment == "SAFE":
            headline = "Conditions look calmer, but this is not a confirmed safe departure window."
            actions.append("Check again immediately before leaving, because weather and sea conditions can change.")
        else:
            headline = "Do not use this result alone to decide whether to leave for sea."
            actions.append("Wait for complete weather and sea information, then run the safety check again.")

        if score is not None and float(score) >= 35:
            reasons.append({"title": "Boat and sea conditions need caution", "text": "The combined boat-and-sea check is above the normal caution level."})
        if (weather.get("precipitationProbability") or 0) >= 70:
            reasons.append({"title": "Rain or storm conditions may affect visibility", "text": "Heavy rain can make it harder to see and conditions may change quickly."})
        if (weather.get("windGustKmh") or 0) >= 40:
            reasons.append({"title": "Strong gusts may make handling harder", "text": "Wind gusts are high enough to trigger the operating caution rule."})
        if (marine.get("waveHeightM") or 0) >= 2 or (marine.get("swellHeightM") or 0) >= 2:
            reasons.append({"title": "Rougher sea movement is expected", "text": "Waves or swell are high enough to make vessel movement less predictable."})
        if (marine.get("currentSpeedMs") or 0) >= 1.5:
            reasons.append({"title": "Strong current may affect control", "text": "The modeled current can make steering and fuel planning harder."})
        if not reasons:
            reasons.append({"title": "Use the latest check before departure", "text": "The available conditions do not show a configured severe trigger, but they can change before you leave."})
        if safety.get("officialWarning", {}).get("state") == "UNAVAILABLE":
            reasons.append({"title": "Official warning status is not confirmed", "text": "Check official harbour or IMD warnings before departing."})
        if geo.get("status") not in {None, "SAFE_INSIDE_BORDER"}:
            actions.append("Keep clear of the restricted areas marked on the map.")
        actions.append("Take enough fuel, communication equipment, and a plan to return early if conditions worsen.")
        return {"headline": headline, "reasons": reasons[:3], "actions": actions[:3]}

    async def analyze(self, context: AgentContext) -> AgentResult:
        prior = context.prior_results
        safety = prior.get("safety_evidence", {}).get("data", prior.get("safety_evidence", {}))
        geo_result = prior.get("geospatial", {}).get("data", prior.get("geospatial", {}))
        # The geospatial agent returns the status under ``geofence`` and map
        # geometry beside it.  Keep those roles separate: safety narration
        # consumes the verified status while the map keeps the geometry.
        geo = geo_result.get("geofence", geo_result) if isinstance(geo_result, dict) else {}
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
        geofence_hazards_query = intent == "geofence_hazards"
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
                f"Local conditions briefing: {', '.join(condition_facts) if condition_facts else ('model sources are live, but no readable point values were returned for this check' if model_evidence_available else 'operational model evidence is unavailable')}. "
                "Tide-gauge data is unavailable at this point; any sea-level value shown is modeled, not a local tide observation. "
                "Open-Meteo supplies modeled wind, waves, currents, and sea level; it is not an official IMD warning feed. "
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
                    "This is model evidence, not an official warning. It cannot confirm lightning strikes or a cyclone advisory. Official IMD warning verification is unavailable, so alert clearance cannot be confirmed."
                )
        elif geofence_hazards_query:
            geofence_status = geo.get("status", "UNAVAILABLE")
            geofence_message = geo.get("message", "Known EEZ/MPA boundary evidence could not be evaluated.")
            if geofence_status == "SAFE_INSIDE_BORDER":
                boundary_guidance = (
                    "No known EEZ-boundary or named-MPA restriction was triggered at the selected point. "
                    "This is selected-point coverage only, not a clearance for every fishing zone or the full route."
                )
            elif geofence_status == "UNAVAILABLE":
                boundary_guidance = "Known EEZ/MPA boundary evidence is unavailable, so no boundary-clearance claim can be made."
            else:
                boundary_guidance = f"Known boundary restriction: {geofence_message}"
            summary = (
                f"Avoid-zone check: marine safety assessment is {assessment} with certification {certification}. "
                f"{boundary_guidance} Official IMD warning verification is unavailable."
            )
        if geofence_hazards_query:
            if geo.get("status") in {"INSIDE_MPA", "OUTSIDE_EEZ", "WARNING"}:
                directive = "Keep clear of the verified boundary or restricted area shown on the map; choose another location or route before departure."
            elif geo.get("status") == "SAFE_INSIDE_BORDER":
                directive = "Check the whole planned route, not only this point, and avoid any verified boundary warnings shown on the map."
            else:
                directive = "Do not treat this as boundary clearance until known EEZ and MPA evidence can be checked."
        elif alerts_query:
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
            "geofences": geo_result.get("geojson", {"type": "FeatureCollection", "features": []}) if isinstance(geo_result, dict) else {"type": "FeatureCollection", "features": []},
            "overlayLayers": [],
            "bsiGrid": map_evidence.get("bsiGrid"),
            "windVectors": map_evidence.get("windVectors"),
            "currentVectors": map_evidence.get("currentVectors"),
            "safetyMapState": {key: value for key, value in map_evidence.items() if key in {"source", "state", "fetchedAt", "reason", "unavailableCells"}},
            "safetyEvidence": {**safety, "geofence": geo},
            "explainability": self._decision_explanation(safety, geo),
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
                    "fisherman_advisory": self._fisherman_advisory(safety, geo),
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
