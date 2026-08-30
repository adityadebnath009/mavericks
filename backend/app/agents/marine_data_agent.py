import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OceanographicData(BaseModel):
    time: List[datetime]
    wave_height: List[float] = Field(..., description="Significant wave height in meters")
    wave_period: List[float] = Field(..., description="Mean wave period in seconds")
    wave_direction: Optional[List[float]] = Field(None, description="Mean wave direction in degrees")
    sea_surface_temperature: Optional[List[float]] = Field(None, description="SST in Celsius")
    ocean_current_velocity: Optional[List[float]] = Field(None, description="Current speed in m/s")

class MeteorologicalData(BaseModel):
    time: List[datetime]
    wind_speed_10m: List[float] = Field(..., description="Wind speed at 10m height in km/h")
    wind_gusts_10m: List[float] = Field(..., description="Wind gusts at 10m height in km/h")
    precipitation_probability: Optional[List[int]] = Field(default=None, description="Rain probability %")
    weather_code: List[int] = Field(..., description="WMO weather code")
    visibility: List[float] = Field(..., description="Visibility in meters")

class MarineDataDiscoveryAgent:
    def __init__(self):
        self.marine_api_url = "https://marine-api.open-meteo.com/v1/marine"
        self.weather_api_url = "https://api.open-meteo.com/v1/forecast"

    async def fetch_oceanographic_data(self, lat: float, lon: float, days: int = 1) -> OceanographicData:
        # Fixed: Explicitly included sea_surface_temperature in hourly parameter
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_period,wave_direction,sea_surface_temperature",
            "forecast_days": days,
            "timezone": "auto"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.marine_api_url, params=params, timeout=8.0)
            response.raise_for_status()
            data = response.json()["hourly"]
            steps = len(data["time"])
            return OceanographicData(
                time=[datetime.fromisoformat(t) for t in data["time"]],
                wave_height=data.get("wave_height", [0.5] * steps),
                wave_period=data.get("wave_period", [5.0] * steps),
                wave_direction=data.get("wave_direction", [0.0] * steps),
                sea_surface_temperature=data.get("sea_surface_temperature"),
                ocean_current_velocity=[0.0] * steps
            )

    async def fetch_meteorological_data(self, lat: float, lon: float, days: int = 1) -> MeteorologicalData:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_gusts_10m,precipitation_probability,weather_code,visibility",
            "forecast_days": days,
            "timezone": "auto"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.weather_api_url, params=params, timeout=8.0)
            response.raise_for_status()
            data = response.json()["hourly"]
            return MeteorologicalData(
                time=[datetime.fromisoformat(t) for t in data["time"]],
                wind_speed_10m=data.get("wind_speed_10m", []),
                wind_gusts_10m=data.get("wind_gusts_10m", []),
                precipitation_probability=data.get("precipitation_probability"),
                weather_code=data.get("weather_code", []),
                visibility=data.get("visibility", [])
            )