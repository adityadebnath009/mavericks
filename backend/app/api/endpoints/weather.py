import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

@router.get("/")
def get_marine_weather(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location")
):
    """
    Fetches real-time and forecasted wave, current, and wind conditions
    from the Open-Meteo Marine & Weather APIs.
    """
    try:
        # 1. Fetch Marine Variables (Waves, Currents, Swell)
        marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction,swell_wave_height,swell_wave_direction,ocean_current_velocity,ocean_current_direction"
        marine_response = requests.get(marine_url, timeout=10)
        
        # 2. Fetch Meteorological Variables (Wind, Precipitation, Temperature)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_direction_10m"
        weather_response = requests.get(weather_url, timeout=10)
        
        if marine_response.status_code != 200 or weather_response.status_code != 200:
            raise HTTPException(
                status_code=502, 
                detail="Failed to retrieve coordinates from weather data services."
            )
            
        marine_data = marine_response.json()
        weather_data = weather_response.json()
        
        current_marine = marine_data.get("current", {})
        current_weather = weather_data.get("current", {})
        
        # 3. Format unified response
        return {
            "coordinates": {"latitude": lat, "longitude": lon},
            "temperature_c": current_weather.get("temperature_2m"),
            "humidity_pct": current_weather.get("relative_humidity_2m"),
            "precipitation_mm": current_weather.get("precipitation"),
            "rain_mm": current_weather.get("rain"),
            "wind": {
                "speed_kmh": current_weather.get("wind_speed_10m"),
                "direction_deg": current_weather.get("wind_direction_10m")
            },
            "sea_state": {
                "wave_height_m": current_marine.get("wave_height"),
                "wave_direction_deg": current_marine.get("wave_direction"),
                "swell_height_m": current_marine.get("swell_wave_height"),
                "swell_direction_deg": current_marine.get("swell_wave_direction"),
                "current_velocity_ms": current_marine.get("ocean_current_velocity"),
                "current_direction_deg": current_marine.get("ocean_current_direction")
            }
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Weather data service connection error: {e}"
        )
