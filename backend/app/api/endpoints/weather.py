import requests
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/")
def get_marine_weather(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
):
    """
    Fetches real-time and forecasted wave, current, and wind conditions
    from the Open-Meteo Marine & Weather APIs. Includes failsafe defaults.
    """
    # Default fallback in case of errors (e.g. land coordinates or connection timeout)
    fallback_data = {
        "coordinates": {"latitude": lat, "longitude": lon},
        "forecast_hourly": {
            "time": [f"Hour {i}" for i in range(72)],
            "wave_height_m": [0.0] * 72,
            "wave_direction_deg": [0.0] * 72,
            "swell_height_m": [0.0] * 72,
            "swell_direction_deg": [0.0] * 72,
            "wave_period_s": [6.0] * 72,
            "wind_speed_kmh": [10.0] * 72,
            "wind_direction_deg": [0.0] * 72
        }
    }
    
    # 1. Fetch Marine Variables (Waves, Swell, Period)
    marine_url = (
        f"https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=wave_height,wave_direction,swell_wave_height,swell_wave_direction,wave_period"
        f"&forecast_days=3"
    )
    
    # 2. Fetch Meteorological Variables (Wind)
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=wind_speed_10m,wind_direction_10m"
        f"&forecast_days=3"
    )
    
    try:
        marine_response = requests.get(marine_url, timeout=5)
        weather_response = requests.get(weather_url, timeout=5)
        
        if marine_response.status_code != 200 or weather_response.status_code != 200:
            # Silent fallback to prevent crashes on land clicks
            return fallback_data
            
        marine_data = marine_response.json()
        weather_data = weather_response.json()
        
        m_hourly = marine_data.get("hourly", {})
        w_hourly = weather_data.get("hourly", {})
        
        # Parse arrays (ensure exactly 72 elements)
        times = m_hourly.get("time", [])[:72]
        wave_heights = [x if x is not None else 0.0 for x in m_hourly.get("wave_height", [])][:72]
        wave_dirs = [x if x is not None else 0.0 for x in m_hourly.get("wave_direction", [])][:72]
        swell_heights = [x if x is not None else 0.0 for x in m_hourly.get("swell_wave_height", [])][:72]
        swell_dirs = [x if x is not None else 0.0 for x in m_hourly.get("swell_wave_direction", [])][:72]
        wave_periods = [x if x is not None else 6.0 for x in m_hourly.get("wave_period", [])][:72]
        
        wind_speeds = [x if x is not None else 10.0 for x in w_hourly.get("wind_speed_10m", [])][:72]
        wind_dirs = [x if x is not None else 0.0 for x in w_hourly.get("wind_direction_10m", [])][:72]
        
        # Pad arrays if less than 72
        length = len(times)
        if length < 72:
            padding = 72 - length
            times += [f"Hour {i}" for i in range(length, 72)]
            wave_heights += [0.0] * padding
            wave_dirs += [0.0] * padding
            swell_heights += [0.0] * padding
            swell_dirs += [0.0] * padding
            wave_periods += [6.0] * padding
            wind_speeds += [10.0] * padding
            wind_dirs += [0.0] * padding
            
        return {
            "coordinates": {"latitude": lat, "longitude": lon},
            "forecast_hourly": {
                "time": times,
                "wave_height_m": wave_heights,
                "wave_direction_deg": wave_dirs,
                "swell_height_m": swell_heights,
                "swell_direction_deg": swell_dirs,
                "wave_period_s": wave_periods,
                "wind_speed_kmh": wind_speeds,
                "wind_direction_deg": wind_dirs
            }
        }
        
    except Exception as e:
        return fallback_data
