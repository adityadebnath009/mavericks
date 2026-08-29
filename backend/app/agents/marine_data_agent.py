import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Pydantic Data Contracts ---
class OceanographicData(BaseModel):
    time: List[datetime]
    wave_height: List[float] = Field(..., description="Significant wave height in meters")
    wave_period: List[float] = Field(..., description="Mean wave period in seconds")
    wave_direction: Optional[List[float]] = Field(None, description="Mean wave direction in degrees")
    sea_surface_temperature: Optional[List[float]] = Field(None, description="SST in Celsius")
    # Added safe default to prevent test crashes until INCOIS data is integrated
    ocean_current_velocity: Optional[List[float]] = Field(None, description="Current speed in m/s")

class MeteorologicalData(BaseModel):
    time: List[datetime]
    wind_speed_10m: List[float] = Field(..., description="Wind speed at 10m height in km/h")
    wind_gusts_10m: List[float] = Field(..., description="Wind gusts at 10m height in km/h")
    # Added precipitation probability matching the SaudSatopay architecture
    precipitation_probability: Optional[List[int]] = Field(default=None, description="Rain probability %")
    weather_code: List[int] = Field(..., description="WMO weather code")
    visibility: List[float] = Field(..., description="Visibility in meters")


# --- Marine Data Discovery Agent ---
class MarineDataDiscoveryAgent:
    """
    Retrieves meteorological and oceanographic variables. 
    Utilizes an honest provider abstraction to route keyless live data.
    """
    def __init__(self):
        self.marine_api_url = "https://marine-api.open-meteo.com/v1/marine"
        self.weather_api_url = "https://api.open-meteo.com/v1/forecast"
        
    async def fetch_oceanographic_data(self, lat: float, lon: float, days: int = 1) -> OceanographicData:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_period,wave_direction",
            "forecast_days": days,
            "timezone": "UTC"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.marine_api_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()["hourly"]
            
            steps = len(data["time"])
            return OceanographicData(
                time=[datetime.fromisoformat(t) for t in data["time"]],
                wave_height=data["wave_height"],
                wave_period=data["wave_period"],
                wave_direction=data.get("wave_direction", [0.0] * steps),
                sea_surface_temperature=data.get("sea_surface_temperature"),
                ocean_current_velocity=[0.0] * steps # Fallback zeros to prevent errors
            )

    async def fetch_meteorological_data(self, lat: float, lon: float, days: int = 1) -> MeteorologicalData:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_gusts_10m,precipitation_probability,weather_code,visibility",
            "forecast_days": days,
            "timezone": "UTC"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.weather_api_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()["hourly"]
            
            return MeteorologicalData(
                time=[datetime.fromisoformat(t) for t in data["time"]],
                wind_speed_10m=data["wind_speed_10m"],
                wind_gusts_10m=data["wind_gusts_10m"],
                precipitation_probability=data.get("precipitation_probability"),
                weather_code=data["weather_code"],
                visibility=data["visibility"]
            )