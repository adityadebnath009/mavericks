import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any

logger = logging.getLogger("open_meteo_client")

class OpenMeteoClient:
    """
    HTTP Client strictly for communicating with Open-Meteo APIs.
    No domain-specific formatting occurs here, only raw data fetching.
    """
    
    MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_FORECAST_DAYS = 3
    
    def __init__(self):
        self.session = requests.Session()
        # Retry strategy: 3 retries, exponential backoff
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
    def fetch_marine_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetches 72-hour marine physics array (Waves, Currents, SST)."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wave_height,wave_period,wave_direction,wind_wave_height,wind_wave_period,wind_wave_direction,swell_wave_height,swell_wave_direction,swell_wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",
            "timezone": "auto",
            "forecast_days": self.OPEN_METEO_FORECAST_DAYS
        }
        try:
            response = self.session.get(self.MARINE_API_URL, params=params, timeout=(2.0, 5.0))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Open-Meteo Marine API failed for {lat},{lon}: {e}")
            raise

    def fetch_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetches 72-hour weather physics array (Wind)."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m,wind_direction_10m",
            "timezone": "auto",
            "forecast_days": self.OPEN_METEO_FORECAST_DAYS
        }
        try:
            response = self.session.get(self.WEATHER_API_URL, params=params, timeout=(2.0, 5.0))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Open-Meteo Weather API failed for {lat},{lon}: {e}")
            raise

open_meteo_client = OpenMeteoClient()
