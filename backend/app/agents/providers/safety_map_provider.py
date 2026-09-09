"""Small, factual safety-map evidence grid for the Intelligence Console."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from app.agents.providers.intelligence_marine_provider import IntelligenceMarineProvider
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentalConditions, EnvironmentSnapshot


class SafetyMapProvider:
    @staticmethod
    def _feature(lon: float, lat: float, properties: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": properties}

    @staticmethod
    def _bsi(weather: Dict[str, Any], marine: Dict[str, Any]) -> float:
        snapshot = EnvironmentSnapshot(current=EnvironmentalConditions(
            timestamp=datetime.now(timezone.utc),
            wave_height_m=float(marine.get("waveHeightM") or 0), wave_period_s=marine.get("wavePeriodS"),
            wave_direction_deg=marine.get("waveDirectionDeg"), wind_wave_height_m=marine.get("windWaveHeightM"),
            wind_wave_period_s=marine.get("windWavePeriodS"), wind_wave_direction_deg=marine.get("windWaveDirectionDeg"),
            swell_wave_height_m=marine.get("swellHeightM"), swell_wave_period_s=marine.get("swellPeriodS"),
            swell_wave_direction_deg=marine.get("swellDirectionDeg"), wind_speed_ms=float(weather.get("windSpeedKmh") or 0) / 3.6,
            wind_direction_deg=weather.get("windDirectionDeg"), current_speed_ms=marine.get("currentSpeedMs"),
            current_direction_deg=marine.get("currentDirectionDeg"),
        ))
        return float(OrcaBsiEngine().evaluate(snapshot, VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=8.0)).get("severity_score", 0))

    async def around(self, lat: float, lon: float) -> Dict[str, Any]:
        # 0.10° is deliberately local (~11 km latitude spacing): this is a
        # decision-support neighborhood, not a fabricated regional forecast.
        points = [(lat + d_lat, lon + d_lon) for d_lat in (-0.10, 0, 0.10) for d_lon in (-0.10, 0, 0.10)]
        provider = IntelligenceMarineProvider()
        values = await asyncio.gather(
            *(provider.collect_safety_evidence(point_lat, point_lon, 1) for point_lat, point_lon in points),
            return_exceptions=True,
        )
        bsi_features, wind_features, current_features = [], [], []
        unavailable = 0
        for (point_lat, point_lon), evidence in zip(points, values):
            if isinstance(evidence, Exception) or evidence["weather"].get("state") == "UNAVAILABLE" or evidence["marine"].get("state") == "UNAVAILABLE":
                unavailable += 1
                continue
            weather, marine = evidence["weather"], evidence["marine"]
            severity = self._bsi(weather, marine)
            bsi_features.append(self._feature(point_lon, point_lat, {
                "severity": severity, "waveHeightM": marine.get("waveHeightM"), "swellHeightM": marine.get("swellHeightM"),
                "fetchedAt": max(weather.get("fetchedAt") or "", marine.get("fetchedAt") or ""),
            }))
            if weather.get("windSpeedKmh") is not None and weather.get("windDirectionDeg") is not None:
                wind_features.append(self._feature(point_lon, point_lat, {"speed_kmh": weather["windSpeedKmh"], "direction_deg": weather["windDirectionDeg"]}))
            if marine.get("currentSpeedMs") is not None and marine.get("currentDirectionDeg") is not None:
                current_features.append(self._feature(point_lon, point_lat, {"speed_ms": marine["currentSpeedMs"], "direction_deg": marine["currentDirectionDeg"]}))
        state = "LIVE" if bsi_features else "UNAVAILABLE"
        return {
            "source": "open_meteo_safety_grid", "state": state, "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "reason": None if state == "LIVE" else "Open-Meteo did not return enough evidence for the local safety grid.",
            "unavailableCells": unavailable,
            "bsiGrid": {"type": "FeatureCollection", "features": bsi_features},
            "windVectors": {"type": "FeatureCollection", "features": wind_features},
            "currentVectors": {"type": "FeatureCollection", "features": current_features},
        }
