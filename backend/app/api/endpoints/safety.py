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
    
    # Generate 3-day peaks
    daily_peaks = {}
    for d in [1, 2, 3]:
        d_date = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
        if d > 1:
            d_date += datetime.timedelta(days=d-1)
        
        peak_score = 0
        peak_rating = "SAFE"
        for h in range(0, 24, 3):
            h_date = d_date.replace(hour=h)
            h_snap = MarineForecastService.get_environment(lat, lon, h_date)
            h_res = engine.evaluate(h_snap, vessel)
            if h_res["severity_score"] > peak_score:
                peak_score = h_res["severity_score"]
                
        if peak_score >= 76:
            peak_rating = "EXTREME"
        elif peak_score >= 51:
            peak_rating = "HIGH"
        elif peak_score >= 21:
            peak_rating = "MODERATE"
            
        daily_peaks[f"day{d}"] = {"score": peak_score, "rating": peak_rating}

    
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
        "daily_peaks": daily_peaks,
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




_global_grid_cache = {}

@router.get("/grid")
@router.get("/grid/")
def get_safety_grid(
    day: int = Query(1, description="Forecast day to evaluate (1, 2, or 3)"),
    hour: int = Query(12, description="Hour of the day (0, 3, 6, 9, 12, 15, 18, 21)")
):
    import numpy as np
    import time
    from app.api.services.open_meteo_client import open_meteo_client
    from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
    from app.api.services.marine_forecast import MarineForecastService
    import datetime
    from scipy.interpolate import griddata
    from global_land_mask import globe
    
    global _global_grid_cache
    cache_key = f"{day}_{hour}_interpolated"
    
    if cache_key in _global_grid_cache:
        timestamp, geojson = _global_grid_cache[cache_key]
        if time.time() - timestamp < 3600:
            return geojson

    # 1. Fetch sparse data at 1.0 degree to avoid API bans
    spacing = 1.0
    target_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=hour, minute=0, second=0, microsecond=0)
    if day > 1:
        target_date += datetime.timedelta(days=day-1)

    coords = []
    # Expand bounding box to fully cover Arabian Sea, Bay of Bengal, and Andaman Sea
    for lat_c in np.arange(5.0, 25.0, spacing):
        for lon_c in np.arange(65.0, 96.0, spacing):
            # Only fetch weather for points that are NOT on land
            if not globe.is_land(lat_c, lon_c):
                coords.append((lat_c, lon_c))

    import concurrent.futures
    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=10.0)
    
    def process_point(c):
        lat, lon = c
        try:
            snap = MarineForecastService.get_environment(lat, lon, target_date)
            res = engine.evaluate(snap, vessel)
            return (lat, lon, res["severity_score"])
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_point, coords))
        
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        return {"type": "FeatureCollection", "features": []}
        
    points = np.array([[r[0], r[1]] for r in valid_results])
    values = np.array([r[2] for r in valid_results])

    # 2. Interpolate to a dense 0.25 degree grid for smooth heatmap
    interp_spacing = 0.25
    grid_lat, grid_lon = np.mgrid[5.0:25.0:interp_spacing, 65.0:96.0:interp_spacing]
    # nearest interpolation prevents edges over land from failing
    grid_z = griddata(points, values, (grid_lat, grid_lon), method='linear')

    features = []
    # 3. Apply exact land mask to the dense grid
    for i in range(grid_lat.shape[0]):
        for j in range(grid_lat.shape[1]):
            lat_c = float(grid_lat[i, j])
            lon_c = float(grid_lon[i, j])
            severity = grid_z[i, j]
            
            if np.isnan(severity):
                continue
                
            # Filter out true land points perfectly
            if globe.is_land(lat_c, lon_c):
                continue

            features.append({
                "type": "Feature",
                "properties": {
                    "severity": int(severity),
                    "bsi": int(severity / 100 * 7) # rough approximation for heatmap weight
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon_c, lat_c]
                }
            })

    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "source": "orca-bsi-grid-interpolated",
            "resolution": interp_spacing
        },
        "features": features
    }
    
    _global_grid_cache[cache_key] = (time.time(), geojson)
    return geojson
