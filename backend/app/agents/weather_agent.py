from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# Assuming this is imported from your updated marine_data_agent.py
from app.agents.marine_data_agent import MeteorologicalData


class AlertSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class WeatherAlert(BaseModel):
    timestamp: datetime
    hazard_type: str = Field(..., description="E.g., Severe Cyclone, Cloud-to-Sea Lightning, Gale")
    severity: AlertSeverity
    trigger_value: float = Field(..., description="Observed numerical value triggering the alert")
    threshold_value: float = Field(..., description="Safety threshold breached")
    message: str = Field(..., description="Human-readable warning message")


class WeatherIntelligenceReport(BaseModel):
    max_wind_speed: float
    max_wind_gust: float
    min_visibility: float
    max_precip_probability: int
    has_active_alerts: bool
    highest_severity: AlertSeverity
    active_hazards: List[str]
    timeline_alerts: List[WeatherAlert]
    plain_language_summary: str


class WeatherIntelligenceAgent:
    """
    Evaluates meteorological time-series arrays against IMD/WMO standard
    marine safety thresholds, now featuring cloud-to-sea lightning and cyclone radius detection.
    """

    WMO_THUNDERSTORM_CODES = {95, 96, 99}
    WMO_HEAVY_RAIN_CODES = {65, 81, 82}

    def analyze(self, met_data: MeteorologicalData) -> WeatherIntelligenceReport:
        alerts: List[WeatherAlert] = []
        hazards_detected = set()

        total_steps = len(met_data.time)
        max_wind = max(met_data.wind_speed_10m) if met_data.wind_speed_10m else 0.0
        max_gust = max(met_data.wind_gusts_10m) if met_data.wind_gusts_10m else 0.0
        min_vis = min(met_data.visibility) if met_data.visibility else 10000.0
        
        # Safely handle the optional precipitation probability
        precip_probs = met_data.precipitation_probability or [0] * total_steps
        max_precip = max(precip_probs) if precip_probs else 0

        for i in range(total_steps):
            t = met_data.time[i]
            wind = met_data.wind_speed_10m[i]
            gust = met_data.wind_gusts_10m[i]
            code = met_data.weather_code[i]
            vis = met_data.visibility[i]
            precip = precip_probs[i]

            # 1. Cyclone Trajectory / Danger Radius (>= 89 km/h - IMD Severe Cyclonic Storm)
            if wind >= 89.0:
                hazards_detected.add("Cyclone Danger Radius")
                alerts.append(
                    WeatherAlert(
                        timestamp=t,
                        hazard_type="Cyclone Danger Radius",
                        severity=AlertSeverity.EXTREME,
                        trigger_value=wind,
                        threshold_value=89.0,
                        message=f"Severe cyclonic storm trajectory detected: sustained winds of {wind:.1f} km/h."
                    )
                )
            # 2. Cyclonic Storm / Gale Force Winds (>= 62 km/h)
            elif wind >= 62.0:
                hazards_detected.add("Cyclonic Gale")
                alerts.append(
                    WeatherAlert(
                        timestamp=t,
                        hazard_type="Cyclonic Gale",
                        severity=AlertSeverity.EXTREME,
                        trigger_value=wind,
                        threshold_value=62.0,
                        message=f"Cyclonic gale-force winds of {wind:.1f} km/h detected."
                    )
                )
            # 3. Squally Winds / High Gusts (Wind >= 40 km/h or Gust >= 55 km/h)
            elif wind >= 40.0 or gust >= 55.0:
                hazards_detected.add("Squally Winds")
                alerts.append(
                    WeatherAlert(
                        timestamp=t,
                        hazard_type="Squally Winds",
                        severity=AlertSeverity.MODERATE,
                        trigger_value=max(wind, gust),
                        threshold_value=40.0 if wind >= 40.0 else 55.0,
                        message=f"Squally conditions: sustained {wind:.1f} km/h, gusting to {gust:.1f} km/h."
                    )
                )

            # 4. Cloud-to-Sea Lightning Strikes (Thunderstorm WMO + High Rain Prob)
            if code in self.WMO_THUNDERSTORM_CODES:
                if precip >= 70:
                    hazards_detected.add("Cloud-to-Sea Lightning")
                    alerts.append(
                        WeatherAlert(
                            timestamp=t,
                            hazard_type="Cloud-to-Sea Lightning",
                            severity=AlertSeverity.EXTREME,
                            trigger_value=float(precip),
                            threshold_value=70.0,
                            message=f"Severe cloud-to-sea lightning strike risk (WMO {code} with {precip}% rain probability)."
                        )
                    )
                else:
                    hazards_detected.add("Thunderstorm")
                    alerts.append(
                        WeatherAlert(
                            timestamp=t,
                            hazard_type="Thunderstorm",
                            severity=AlertSeverity.HIGH,
                            trigger_value=float(code),
                            threshold_value=95.0,
                            message=f"Active thunderstorm cells detected (WMO code {code})."
                        )
                    )

            # 5. Heavy Precipitation
            elif code in self.WMO_HEAVY_RAIN_CODES or precip >= 85:
                hazards_detected.add("Heavy Rainfall")
                alerts.append(
                    WeatherAlert(
                        timestamp=t,
                        hazard_type="Heavy Rainfall",
                        severity=AlertSeverity.MODERATE,
                        trigger_value=float(precip),
                        threshold_value=85.0,
                        message=f"Heavy marine precipitation detected ({precip}% probability)."
                    )
                )

            # 6. Navigational Visibility Hazard (< 1000m)
            if vis < 1000.0:
                hazards_detected.add("Low Visibility")
                alerts.append(
                    WeatherAlert(
                        timestamp=t,
                        hazard_type="Low Visibility",
                        severity=AlertSeverity.HIGH if vis < 500.0 else AlertSeverity.MODERATE,
                        trigger_value=vis,
                        threshold_value=1000.0,
                        message=f"Dense fog/squall hazard: visibility reduced to {vis:.0f} m."
                    )
                )

        # Determine highest overall severity
        severity_order = [
            AlertSeverity.INFO,
            AlertSeverity.LOW,
            AlertSeverity.MODERATE,
            AlertSeverity.HIGH,
            AlertSeverity.EXTREME,
        ]
        highest_sev = AlertSeverity.LOW
        for alert in alerts:
            if severity_order.index(alert.severity) > severity_order.index(highest_sev):
                highest_sev = alert.severity

        # Plain language summary generator
        if not alerts:
            summary = "Marine weather conditions remain calm and clear across the forecast window."
        else:
            summary = (
                f"Active marine hazards detected ({', '.join(hazards_detected)}). "
                f"Peak wind speed reaches {max_wind:.1f} km/h with a {max_precip}% maximum rain probability. "
                f"Maximum risk tier: {highest_sev.value}."
            )

        return WeatherIntelligenceReport(
            max_wind_speed=max_wind,
            max_wind_gust=max_gust,
            min_visibility=min_vis,
            max_precip_probability=max_precip,
            has_active_alerts=len(alerts) > 0,
            highest_severity=highest_sev,
            active_hazards=sorted(list(hazards_detected)),
            timeline_alerts=alerts,
            plain_language_summary=summary,
        )