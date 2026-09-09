"""Fast, agent-only marine evidence provider.

This module deliberately does not use the existing INCOIS proxy, OpenDAP, WMS,
or netCDF path.  Those integrations remain owned by the established dashboard
workflows.  The Intelligence Console uses short-lived Open-Meteo evidence and
an isolated in-memory cache so a conversational request cannot overload them.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import httpx


class IntelligenceMarineProvider:
    _cache: Dict[Tuple[str, float, float, str], Tuple[float, Dict[str, Any]]] = {}
    _weather_url = "https://api.open-meteo.com/v1/forecast"
    _marine_url = "https://marine-api.open-meteo.com/v1/marine"

    @staticmethod
    def _key(source: str, lat: float, lon: float, window: str) -> Tuple[str, float, float, str]:
        return source, round(lat, 2), round(lon, 2), window

    async def _cached(self, source: str, lat: float, lon: float, window: str, ttl_seconds: int, fetcher):
        key = self._key(source, lat, lon, window)
        cached = self._cache.get(key)
        now = time.monotonic()
        age_seconds = round(now - cached[0], 1) if cached else None
        if cached and age_seconds <= ttl_seconds:
            return {**cached[1], "source": source, "state": "CACHED", "cacheAgeSeconds": age_seconds}
        try:
            result = await fetcher()
        except Exception as exc:
            # A previous observation is useful for context but is never
            # silently promoted to live data after a provider failure.
            if cached:
                return {**cached[1], "source": source, "state": "STALE", "cacheAgeSeconds": age_seconds,
                        "reason": f"Live refresh failed: {exc}"}
            raise
        self._cache[key] = (now, result)
        return {**result, "source": source, "state": "LIVE", "cacheAgeSeconds": 0}

    async def weather(self, lat: float, lon: float, forecast_days: int) -> Dict[str, Any]:
        async def fetch():
            params = {
                "latitude": lat, "longitude": lon, "forecast_days": forecast_days,
                "timezone": "UTC", "cell_selection": "sea",
                "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation_probability,precipitation,weather_code,visibility,pressure_msl,cape",
            }
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(self._weather_url, params=params)
                response.raise_for_status()
                hourly = response.json().get("hourly", {})
            values = lambda name: [v for v in hourly.get(name, []) if v is not None]
            return {
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "windSpeedKmh": max(values("wind_speed_10m") or [None]),
                "windDirectionDeg": values("wind_direction_10m")[0] if values("wind_direction_10m") else None,
                "windGustKmh": max(values("wind_gusts_10m") or [None]),
                "visibilityM": min(values("visibility") or [None]),
                "precipitationProbability": max(values("precipitation_probability") or [None]),
                "cape": max(values("cape") or [None]),
                "weatherCodes": values("weather_code"),
            }
        try:
            return await self._cached("open_meteo_weather", lat, lon, str(forecast_days), 900, fetch)
        except Exception as exc:
            return {"source": "open_meteo_weather", "state": "UNAVAILABLE", "reason": str(exc)}

    async def marine(self, lat: float, lon: float, forecast_days: int) -> Dict[str, Any]:
        async def fetch():
            params = {
                "latitude": lat, "longitude": lon, "forecast_days": forecast_days,
                "timezone": "UTC",
                "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,secondary_swell_wave_height,secondary_swell_wave_direction,secondary_swell_wave_period,tertiary_swell_wave_height,tertiary_swell_wave_direction,tertiary_swell_wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature,sea_level_height_msl",
            }
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(self._marine_url, params=params)
                response.raise_for_status()
                hourly = response.json().get("hourly", {})
            values = lambda name: [v for v in hourly.get(name, []) if v is not None]
            return {
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "waveHeightM": max(values("wave_height") or [None]),
                "waveDirectionDeg": values("wave_direction")[0] if values("wave_direction") else None,
                "wavePeriodS": max(values("wave_period") or [None]),
                "windWaveHeightM": max(values("wind_wave_height") or [None]),
                "windWaveDirectionDeg": values("wind_wave_direction")[0] if values("wind_wave_direction") else None,
                "windWavePeriodS": max(values("wind_wave_period") or [None]),
                "swellHeightM": max(values("swell_wave_height") or [None]),
                "swellDirectionDeg": values("swell_wave_direction")[0] if values("swell_wave_direction") else None,
                "swellPeriodS": max(values("swell_wave_period") or [None]),
                "secondarySwellHeightM": max(values("secondary_swell_wave_height") or [None]),
                "secondarySwellDirectionDeg": values("secondary_swell_wave_direction")[0] if values("secondary_swell_wave_direction") else None,
                "secondarySwellPeriodS": max(values("secondary_swell_wave_period") or [None]),
                "tertiarySwellHeightM": max(values("tertiary_swell_wave_height") or [None]),
                "tertiarySwellDirectionDeg": values("tertiary_swell_wave_direction")[0] if values("tertiary_swell_wave_direction") else None,
                "tertiarySwellPeriodS": max(values("tertiary_swell_wave_period") or [None]),
                "currentSpeedMs": max(values("ocean_current_velocity") or [None]),
                "currentDirectionDeg": values("ocean_current_direction")[0] if values("ocean_current_direction") else None,
                "seaSurfaceTemperatureC": max(values("sea_surface_temperature") or [None]),
                "seaLevelHeightMslM": max(values("sea_level_height_msl") or [None]),
            }
        try:
            return await self._cached("open_meteo_marine", lat, lon, str(forecast_days), 900, fetch)
        except Exception as exc:
            return {"source": "open_meteo_marine", "state": "UNAVAILABLE", "reason": str(exc)}

    async def collect_safety_evidence(self, lat: float, lon: float, forecast_days: int) -> Dict[str, Dict[str, Any]]:
        weather, marine = await asyncio.gather(
            self.weather(lat, lon, forecast_days), self.marine(lat, lon, forecast_days)
        )
        return {"weather": weather, "marine": marine}
