"""Console-only safety evidence and BSI assessment agent."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.agents.providers.intelligence_marine_provider import IntelligenceMarineProvider
from app.agents.providers.safety_map_provider import SafetyMapProvider
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentalConditions, EnvironmentSnapshot
from datetime import datetime, timezone


class SafetyEvidenceAgent(AbstractAgent):
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(name="safety_evidence", dependencies=[], mode_support=["fisheries", "routing", "weather"])

    @staticmethod
    def _assessment(weather: Dict[str, Any], marine: Dict[str, Any], bsi_score: float, ml_class: str) -> str:
        if weather.get("state") == "UNAVAILABLE" or marine.get("state") == "UNAVAILABLE":
            return "PARTIAL"
        if ml_class in {"HIGH", "EXTREME"} or bsi_score >= 85 or (weather.get("windGustKmh") or 0) >= 55 or (marine.get("waveHeightM") or 0) >= 3.5:
            return "UNSAFE"
        if ml_class == "MODERATE" or bsi_score >= 35 or (weather.get("windGustKmh") or 0) >= 40 or (marine.get("waveHeightM") or 0) >= 2.0:
            return "CAUTION"
        return "SAFE"

    @staticmethod
    def _ml_risk(snapshot: EnvironmentSnapshot, weather: Dict[str, Any], marine: Dict[str, Any]) -> Dict[str, Any]:
        """Use the existing trained model without adding it to the legacy DAG."""
        from app.agents.risk_agent import RiskAnalysisAgent

        compatible_weather = {"data": {
            "max_wind_speed": weather.get("windSpeedKmh"),
            "gust_speed": weather.get("windGustKmh"),
        }}
        compatible_ocean = {"data": {"base_wave_height": marine.get("waveHeightM")}}
        return RiskAnalysisAgent()._predict_ml_risk(snapshot, compatible_weather, compatible_ocean)

    async def analyze(self, context: AgentContext) -> AgentResult:
        started = time.perf_counter()
        days = 3 if context.temporal.mode == "forecast" else 1
        evidence, map_evidence = await asyncio.gather(
            IntelligenceMarineProvider().collect_safety_evidence(context.latitude, context.longitude, days),
            SafetyMapProvider().around(context.latitude, context.longitude),
        )
        weather, marine = evidence["weather"], evidence["marine"]
        critical_available = weather.get("state") != "UNAVAILABLE" and marine.get("state") != "UNAVAILABLE"
        snapshot = EnvironmentSnapshot(
            current=EnvironmentalConditions(
                timestamp=datetime.now(timezone.utc),
                wave_height_m=float(marine.get("waveHeightM") or 0),
                wave_period_s=marine.get("wavePeriodS"),
                wave_direction_deg=marine.get("waveDirectionDeg"),
                wind_wave_height_m=marine.get("windWaveHeightM"),
                wind_wave_period_s=marine.get("windWavePeriodS"),
                wind_wave_direction_deg=marine.get("windWaveDirectionDeg"),
                swell_wave_height_m=marine.get("swellHeightM"),
                swell_wave_period_s=marine.get("swellPeriodS"),
                swell_wave_direction_deg=marine.get("swellDirectionDeg"),
                wind_speed_ms=float(weather.get("windSpeedKmh") or 0) / 3.6,
                wind_direction_deg=weather.get("windDirectionDeg"),
                current_speed_ms=marine.get("currentSpeedMs"),
                current_direction_deg=marine.get("currentDirectionDeg"),
            )
        )
        bsi = OrcaBsiEngine().evaluate(snapshot, VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=8.0))
        bsi_score = float(bsi.get("severity_score", 0))
        ml_risk = self._ml_risk(snapshot, weather, marine)
        ml_class = ml_risk.get("ml_risk_class", "UNKNOWN")
        deterministic_class = "EXTREME" if bsi_score >= 85 else ("HIGH" if bsi_score >= 60 else ("MODERATE" if bsi_score >= 35 else "LOW"))
        class_rank = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "EXTREME": 3}
        safety_floor_triggered = critical_available and class_rank.get(deterministic_class, 0) > class_rank.get(ml_class, 0)
        bsi["ml_assessment"] = ml_risk
        bsi["deterministic_class"] = deterministic_class
        bsi["isSafetyFloorTriggered"] = safety_floor_triggered
        assessment = self._assessment(weather, marine, bsi_score, ml_class)
        hazards = []
        if (weather.get("windGustKmh") or 0) >= 40:
            hazards.append("Strong wind gusts")
        if (weather.get("precipitationProbability") or 0) >= 70:
            hazards.append("High precipitation probability")
        if (marine.get("waveHeightM") or 0) >= 2:
            hazards.append("Elevated significant wave height")
        if (marine.get("swellHeightM") or 0) >= 2:
            hazards.append("Elevated swell height")
        if (marine.get("currentSpeedMs") or 0) >= 1.5:
            hazards.append("Strong modeled ocean current")
        if (weather.get("visibilityM") or float("inf")) < 1000:
            hazards.append("Low visibility")
        payload = {
            "assessment": assessment,
            # IMD official-warning verification is not available yet.  A
            # model-based assessment must therefore never be certified safe.
            "certification": "PARTIAL",
            # The engine may still calculate an internal diagnostic from
            # defaults, but that is not a displayable Boat Safety Index when
            # wind/wave evidence is incomplete.
            "bsi": {"severityScore": bsi_score if critical_available else None, "report": bsi},
            "mlRisk": ml_risk,
            "bsiEvidence": {"source": "orca_bsi_engine", "state": "LIVE" if critical_available else "UNAVAILABLE",
                            "reason": None if critical_available else "Boat Safety Index is unavailable because critical weather or marine evidence is missing."},
            "mlEvidence": {"source": "xgboost_ml_model", "state": "LIVE" if ml_risk.get("model_status") == "ML_ACTIVE" else "UNAVAILABLE",
                           "reason": None if ml_risk.get("model_status") == "ML_ACTIVE" else "The trained XGBoost model is unavailable; deterministic fallback is not an ML result."},
            "weather": weather,
            "marine": marine,
            "hazards": hazards,
            "criticalEvidenceAvailable": critical_available,
            "officialWarning": {"source": "imd", "state": "UNAVAILABLE", "reason": "IMD access and IP whitelisting are pending."},
            "mapEvidence": map_evidence,
        }
        return AgentResult(agent_name=self.spec.name, status="success", data=payload,
                           latency_ms=round((time.perf_counter() - started) * 1000, 2),
                           sources=[weather.get("source", "open_meteo_weather"), marine.get("source", "open_meteo_marine"), "orca_bsi_engine", "xgboost_ml_model"])
