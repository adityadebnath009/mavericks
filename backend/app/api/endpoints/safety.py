import os
import json
import time
import math
import requests
import datetime
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.endpoints.geofence import check_geofence_status
from app.api.services.marine_forecast import MarineForecastService
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile

logger = logging.getLogger(__name__)

CACHE_DIR_ADV = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
ADVISORY_CACHE = os.path.join(CACHE_DIR_ADV, "svas_advisory.json")

router = APIRouter()

@router.get("")
@router.get("/")
def get_safety_assessment(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    beam: float = Query(None, description="Beam width of the vessel in meters"),
    day: int = Query(1, description="Forecast day to evaluate (1, 2, or 3)"),
    hour: int = Query(12, description="Forecast hour to evaluate (0, 3, 6, 9, 12, 15, 18, 21)"),
    db: Session = Depends(get_db)
):
    geofence = check_geofence_status(lat, lon, db)
    
    target_date = datetime.datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
    if day > 1:
        target_date += datetime.timedelta(days=day-1)

    snapshot = MarineForecastService.get_environment(lat, lon, target_date)
    
    length_m = 15.0
    beam_m = beam if beam else 4.0
    vessel = VesselProfile(length_m=length_m, beam_m=beam_m, cruising_speed_kn=10.0)
    engine = OrcaBsiEngine()
    
    orca_result = engine.evaluate(snapshot, vessel)
    
    inspect_hs = snapshot.current.wave_height_m or 0.0
    inspect_wind = (snapshot.current.wind_speed_ms * 3.6) if snapshot.current.wind_speed_ms else 0.0
    inspect_curr = snapshot.current.current_speed_ms or 0.0
    inspect_hsea = snapshot.current.wind_wave_height_m or 0.0
    inspect_mwd = snapshot.current.wave_direction_deg or 0.0

    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "severity_score": orca_result["severity_score"],
        "confidence": orca_result["confidence"],
        "hazards": orca_result["hazards"],
        "available_hazards": orca_result["available_hazards"],
        "unavailable_hazards": orca_result["unavailable_hazards"],
        "orca_risk": orca_result,
        "raw_metrics": {
            "wave_height_m": inspect_hs,
            "wind_speed_kmh": inspect_wind,
            "current_speed_ms": inspect_curr,
            "distance_to_border_km": geofence.get("distance_to_border_km"),
            "is_inside_eez": geofence.get("is_inside_eez"),
            "is_inside_mpa": geofence.get("is_inside_mpa"),
            "mpa_name": geofence.get("mpa_name"),
            
            "inspect_hs": inspect_hs,
            "inspect_hsea": inspect_hsea,
            "inspect_mwd": inspect_mwd,
            "inspect_wind": inspect_wind,
            "inspect_curr": inspect_curr,
            
            "incois_sst": snapshot.current.sst_c,
            "incois_chl": snapshot.current.chl_mg_m3
        }
    }

@router.get("/forecast")
@router.get("/forecast/")
def get_point_forecast_timeline(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    day: int = Query(1, description="Forecast day")
):
    target_date = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
    if day > 1:
        target_date += datetime.timedelta(days=day-1)

    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=10.0)

    timeline_data = []
    
    # Generate 8 steps (every 3 hours)
    for hour in range(0, 24, 3):
        step_date = target_date.replace(hour=hour)
        step_snapshot = MarineForecastService.get_environment(lat, lon, step_date)
        orca_result = engine.evaluate(step_snapshot, vessel)
        
        hs = step_snapshot.current.wave_height_m or 0.0
        wind = (step_snapshot.current.wind_speed_ms * 3.6) if step_snapshot.current.wind_speed_ms else 0.0
        curr = step_snapshot.current.current_speed_ms or 0.0

        timeline_data.append({
            "time": f"{hour:02d}:00",
            "bsi": orca_result["severity_score"],
            "severity_score": orca_result["severity_score"],
            "wave_height": round(hs, 2),
            "wind_speed": round(wind, 1),
            "current_speed": round(curr, 2)
        })

    return timeline_data

@router.get("/advisories")
@router.get("/advisories/")
def get_coastal_advisories():
    os.makedirs(CACHE_DIR_ADV, exist_ok=True)
    if os.path.exists(ADVISORY_CACHE):
        try:
            if time.time() - os.path.getmtime(ADVISORY_CACHE) < 86400:
                with open(ADVISORY_CACHE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

    url = "https://www.incois.gov.in/oceanservices/SVAS/SVAS_Advisory.geojson"
    try:
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            with open(ADVISORY_CACHE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return data
    except Exception:
        pass

    if os.path.exists(ADVISORY_CACHE):
        try:
            with open(ADVISORY_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "type": "FeatureCollection",
        "name": "SVAS_Advisory_Fallback",
        "features": []
    }

@router.get("/grid")
@router.get("/grid/")
def get_safety_grid(
    day: int = Query(1, description="Forecast day to evaluate (1, 2, or 3)"),
    hour: int = Query(12, description="Hour of the day (0, 3, 6, 9, 12, 15, 18, 21)")
):
    import numpy as np
    features = []
    spacing = 0.5
    half = spacing / 2.0

    target_date = datetime.datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
    if day > 1:
        target_date += datetime.timedelta(days=day-1)

    for lat_c in np.arange(6.0, 23.0, spacing):
        for lon_c in np.arange(68.0, 93.0, spacing):
            is_land = False
            if 8.5 <= lat_c <= 22.0:
                if lat_c <= 15.0:
                    center_lon = 77.5
                    width = 2.0 + (lat_c - 8.5) * 0.8
                    if abs(lon_c - center_lon) < width:
                        is_land = True
                elif lat_c <= 22.0:
                    if 72.5 <= lon_c <= 86.5:
                        is_land = True
            if 6.0 <= lat_c <= 9.5 and 79.5 <= lon_c <= 82.0:
                is_land = True

            if is_land:
                continue

            base_hs = 1.0 + 1.2 * math.sin(lat_c * 0.2 + lon_c * 0.15 + day * 0.5 + hour * 0.1)
            base_hs = max(0.5, min(4.2, base_hs))
            
            severity = min(int((base_hs / 4.0) * 100), 100)
            
            if severity >= 76:
                color = "red"
            elif severity >= 51:
                color = "red"
            elif severity >= 21:
                color = "orange"
            else:
                color = "green"
            
            coords = [
                [round(float(lon_c - half), 4), round(float(lat_c - half), 4)],
                [round(float(lon_c + half), 4), round(float(lat_c - half), 4)],
                [round(float(lon_c + half), 4), round(float(lat_c + half), 4)],
                [round(float(lon_c - half), 4), round(float(lat_c + half), 4)],
                [round(float(lon_c - half), 4), round(float(lat_c - half), 4)]
            ]

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                },
                "properties": {
                    "bsi": severity,
                    "severity_score": severity,
                    "color": color,
                    "center_lat": round(float(lat_c), 4),
                    "center_lon": round(float(lon_c), 4)
                }
            })
            
    return {
        "type": "FeatureCollection",
        "features": features
    }
