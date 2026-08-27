import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Honest Provider Data Contracts ---
class OceanographicData(BaseModel):
    time: List[datetime]
    wave_height: List[float] = Field(..., description="Significant wave height in meters")
    wave_period: List[float] = Field(..., description="Mean wave period in seconds")
    wave_direction: List[float] = Field(..., description="Mean wave direction in degrees")
    swell_wave_height: List[float] = Field(..., description="Swell height in meters")
    ocean_current_velocity: List[float] = Field(..., description="Current speed in m/s")
    ocean_current_direction: List[float] = Field(..., description="Current direction in degrees")
    sea_surface_temperature: Optional[List[float]] = Field(None, description="SST in Celsius")

class MeteorologicalData(BaseModel):
    time: List[datetime]
    wind_speed_10m: List[float] = Field(..., description="Wind speed at 10m height in km/h")
    wind_direction_10m: List[float] = Field(..., description="Wind direction at 10m height in degrees")
    wind_gusts_10m: List[float] = Field(..., description="Wind gusts at 10m height in km/h")
    weather_code: List[int] = Field(..., description="WMO weather code (e.g., storms, rain)")
    visibility: List[float] = Field(..., description="Visibility in meters")


# --- Marine Data Discovery Agent ---
class MarineDataDiscoveryAgent:
    def __init__(self):
        self.marine_api_url = "https://marine-api.open-meteo.com/v1/marine"
        self.weather_api_url = "https://api.open-meteo.com/v1/forecast"
        
    async def fetch_oceanographic_data(self, lat: float, lon: float, days: int = 3) -> OceanographicData:
        """Fetches ocean state variables."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_period,wave_direction,swell_wave_height,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",
            "forecast_days": days,
            "timezone": "UTC"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.marine_api_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            hourly = data["hourly"]
            return OceanographicData(
                time=[datetime.fromisoformat(t) for t in hourly["time"]],
                wave_height=hourly["wave_height"],
                wave_period=hourly["wave_period"],
                wave_direction=hourly["wave_direction"],
                swell_wave_height=hourly["swell_wave_height"],
                ocean_current_velocity=hourly["ocean_current_velocity"],
                ocean_current_direction=hourly["ocean_current_direction"],
                sea_surface_temperature=hourly.get("sea_surface_temperature")
            )

    async def fetch_meteorological_data(self, lat: float, lon: float, days: int = 3) -> MeteorologicalData:
        """Fetches atmospheric weather variables."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,weather_code,visibility",
            "forecast_days": days,
            "timezone": "UTC"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.weather_api_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            hourly = data["hourly"]
            return MeteorologicalData(
                time=[datetime.fromisoformat(t) for t in hourly["time"]],
                wind_speed_10m=hourly["wind_speed_10m"],
                wind_direction_10m=hourly["wind_direction_10m"],
                wind_gusts_10m=hourly["wind_gusts_10m"],
                weather_code=hourly["weather_code"],
                visibility=hourly["visibility"]
            )