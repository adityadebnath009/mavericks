import time
from datetime import datetime
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.agents.marine_data_agent import MarineDataDiscoveryAgent, MeteorologicalData

class AlertSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"

class IMDColorCode(str, Enum):
    GREEN = "GREEN (No Warning)"
    YELLOW = "YELLOW (Be Updated / Watch)"
    ORANGE = "ORANGE (Be Prepared / Alert)"
    RED = "RED (Take Action / Warning)"

class WeatherAlert(BaseModel):
    timestamp: datetime
    hazard_type: str
    severity: AlertSeverity
    trigger_value: float
    threshold_value: float
    message: str

class HazardStatus(BaseModel):
    active: bool
    severity: Optional[str] = None

class Hazards(BaseModel):
    cyclone: HazardStatus
    lightning: HazardStatus
    heavy_rain: HazardStatus

class WeatherIntelligenceReport(BaseModel):
    max_wind_speed: float
    max_wind_gust: float
    min_visibility: float
    max_precip_probability: int
    has_active_alerts: bool
    highest_severity: AlertSeverity
    imd_color_code: IMDColorCode
    weather_safety_score: int = Field(..., description="0 (Deadly) to 100 (Optimal)")
    hazards: Hazards
    timeline_alerts: List[WeatherAlert]
    hourly_risk_curve: List[int]
    plain_language_summary: str

class WeatherIntelligenceAgent(AbstractAgent):
    WMO_THUNDERSTORM_CODES = {95, 96, 99}
    WMO_HEAVY_RAIN_CODES = {65, 81, 82}

    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="weather",
            dependencies=[],
            mode_support=["fisheries", "weather", "routing"]
        )

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        lat = context.latitude
        lon = context.longitude
        
        if lat is None or lon is None:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=["Latitude and longitude are required in context."]
            )
            
        try:
            discovery = MarineDataDiscoveryAgent()
            # Dynamic forecasting horizon based on LLM semantic time window
            days = 3 if context.temporal.mode == "forecast" else 1
            met_data = await discovery.fetch_meteorological_data(lat, lon, days=days)
            
            # Slice the data to strictly match the requested temporal context window
            if context.temporal.start_time and context.temporal.end_time:
                from datetime import timezone
                start = context.temporal.start_time.replace(tzinfo=timezone.utc)
                end = context.temporal.end_time.replace(tzinfo=timezone.utc)
                filtered_indices = [
                    i for i, t in enumerate(met_data.time) 
                    if start <= t.replace(tzinfo=timezone.utc) <= end
                ]
                if filtered_indices:
                    met_data.time = [met_data.time[i] for i in filtered_indices]
                    met_data.wind_speed_10m = [met_data.wind_speed_10m[i] for i in filtered_indices]
                    met_data.wind_gusts_10m = [met_data.wind_gusts_10m[i] for i in filtered_indices]
                    if met_data.precipitation_probability:
                        met_data.precipitation_probability = [met_data.precipitation_probability[i] for i in filtered_indices]
                    met_data.weather_code = [met_data.weather_code[i] for i in filtered_indices]
                    met_data.visibility = [met_data.visibility[i] for i in filtered_indices]
                    
            report = self._analyze_logic(met_data)
            latency = (time.perf_counter() - start_time) * 1000
            
            return AgentResult(
                agent_name=self.spec.name,
                status="success",
                data=report.model_dump(),
                latency_ms=round(latency, 2),
                sources=["open-meteo"],
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=[str(e)]
            )

    def _analyze_logic(self, met_data: MeteorologicalData) -> WeatherIntelligenceReport:
        alerts: List[WeatherAlert] = []
        hazards_detected = set()
        hourly_risk_curve: List[int] = []
        
        total_steps = len(met_data.time)
        max_wind = max(met_data.wind_speed_10m) if met_data.wind_speed_10m else 0.0
        max_gust = max(met_data.wind_gusts_10m) if met_data.wind_gusts_10m else 0.0
        min_vis = min(met_data.visibility) if met_data.visibility else 10000.0
        precip_probs = met_data.precipitation_probability or [0] * total_steps
        max_precip = max(precip_probs) if precip_probs else 0

        for i in range(total_steps):
            t = met_data.time[i]
            wind = met_data.wind_speed_10m[i]
            gust = met_data.wind_gusts_10m[i]
            code = met_data.weather_code[i]
            vis = met_data.visibility[i]
            precip = precip_probs[i]

            step_risk = 10 # Base calm risk (0-100 scale)

            if wind >= 89.0:
                hazards_detected.add("Cyclone Danger Radius")
                step_risk = max(step_risk, 95)
                alerts.append(WeatherAlert(
                    timestamp=t, hazard_type="Cyclone Danger Radius", severity=AlertSeverity.EXTREME,
                    trigger_value=wind, threshold_value=89.0,
                    message=f"Severe cyclonic storm trajectory: sustained {wind:.1f} km/h."
                ))
            elif wind >= 62.0:
                hazards_detected.add("Cyclonic Gale")
                step_risk = max(step_risk, 85)
                alerts.append(WeatherAlert(
                    timestamp=t, hazard_type="Cyclonic Gale", severity=AlertSeverity.EXTREME,
                    trigger_value=wind, threshold_value=62.0,
                    message=f"Gale-force winds of {wind:.1f} km/h detected."
                ))
            elif wind >= 40.0 or gust >= 55.0:
                hazards_detected.add("Squally Winds")
                step_risk = max(step_risk, 55)
                alerts.append(WeatherAlert(
                    timestamp=t, hazard_type="Squally Winds", severity=AlertSeverity.MODERATE,
                    trigger_value=max(wind, gust), threshold_value=40.0,
                    message=f"Squally conditions: sustained {wind:.1f} km/h, gusting {gust:.1f} km/h."
                ))

            if code in self.WMO_THUNDERSTORM_CODES:
                if precip >= 70:
                    hazards_detected.add("Cloud-to-Sea Lightning")
                    step_risk = max(step_risk, 90)
                    alerts.append(WeatherAlert(
                        timestamp=t, hazard_type="Cloud-to-Sea Lightning", severity=AlertSeverity.EXTREME,
                        trigger_value=float(precip), threshold_value=70.0,
                        message=f"Severe electrical hazard: lightning cells with {precip}% rain probability."
                    ))
                else:
                    hazards_detected.add("Thunderstorm")
                    step_risk = max(step_risk, 65)
                    alerts.append(WeatherAlert(
                        timestamp=t, hazard_type="Thunderstorm", severity=AlertSeverity.HIGH,
                        trigger_value=float(code), threshold_value=95.0,
                        message=f"Active convective storm cells (WMO {code})."
                    ))
            elif code in self.WMO_HEAVY_RAIN_CODES or precip >= 85:
                hazards_detected.add("Heavy Rainfall")
                step_risk = max(step_risk, 45)
                alerts.append(WeatherAlert(
                    timestamp=t, hazard_type="Heavy Rainfall", severity=AlertSeverity.MODERATE,
                    trigger_value=float(precip), threshold_value=85.0,
                    message=f"Heavy marine precipitation ({precip}% probability)."
                ))

            if vis < 1000.0:
                hazards_detected.add("Low Visibility")
                step_risk = max(step_risk, 60 if vis < 500 else 40)
                alerts.append(WeatherAlert(
                    timestamp=t, hazard_type="Low Visibility",
                    severity=AlertSeverity.HIGH if vis < 500.0 else AlertSeverity.MODERATE,
                    trigger_value=vis, threshold_value=1000.0,
                    message=f"Navigational fog hazard: visibility {vis:.0f}m."
                ))

            hourly_risk_curve.append(step_risk)

        peak_risk = max(hourly_risk_curve) if hourly_risk_curve else 0
        overall_safety = max(0, 100 - peak_risk)

        if peak_risk >= 80:
            imd_tier = IMDColorCode.RED
            highest_sev = AlertSeverity.EXTREME
        elif peak_risk >= 55:
            imd_tier = IMDColorCode.ORANGE
            highest_sev = AlertSeverity.HIGH
        elif peak_risk >= 35:
            imd_tier = IMDColorCode.YELLOW
            highest_sev = AlertSeverity.MODERATE
        else:
            imd_tier = IMDColorCode.GREEN
            highest_sev = AlertSeverity.LOW

        
        cyclone_active = "Cyclone Danger Radius" in hazards_detected or "Cyclonic Gale" in hazards_detected
        cyclone_sev = "extreme" if cyclone_active else None
        
        lightning_active = "Cloud-to-Sea Lightning" in hazards_detected or "Thunderstorm" in hazards_detected
        lightning_sev = "extreme" if "Cloud-to-Sea Lightning" in hazards_detected else ("high" if "Thunderstorm" in hazards_detected else None)
        
        heavy_rain_active = "Heavy Rainfall" in hazards_detected
        heavy_rain_sev = "moderate" if heavy_rain_active else None

        hazards_obj = Hazards(
            cyclone=HazardStatus(active=cyclone_active, severity=cyclone_sev),
            lightning=HazardStatus(active=lightning_active, severity=lightning_sev),
            heavy_rain=HazardStatus(active=heavy_rain_active, severity=heavy_rain_sev)
        )

        summary = (
            "Marine weather conditions remain calm and clear across the forecast window."
            if not alerts else
            f"Active marine hazards detected ({', '.join(sorted(hazards_detected))}). "
            f"Peak wind reaches {max_wind:.1f} km/h with {max_precip}% max rain probability. "
            f"Official IMD advisory level: {imd_tier.value}."
        )

        return WeatherIntelligenceReport(
            max_wind_speed=max_wind,
            max_wind_gust=max_gust,
            min_visibility=min_vis,
            max_precip_probability=max_precip,
            has_active_alerts=len(alerts) > 0,
            highest_severity=highest_sev,
            imd_color_code=imd_tier,
            weather_safety_score=overall_safety,
            hazards=hazards_obj,
            timeline_alerts=alerts,
            hourly_risk_curve=hourly_risk_curve,
            plain_language_summary=summary
        )