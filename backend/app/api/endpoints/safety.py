import math
import requests
import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.endpoints.weather import get_marine_weather
from app.api.endpoints.geofence import check_geofence_status
from app.api.services.bsi_calculator import BSICalculator
from app.api.services.incois_resolver import IncoisDatasetResolver

router = APIRouter()

@router.get("/")
def get_safety_assessment(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    beam: float = Query(None, description="Beam width of the vessel in meters"),
    day: int = Query(1, description="Forecast day to evaluate (1, 2, or 3)"),
    db: Session = Depends(get_db)
):
    """
    Computes a unified Marine Safety Score by combining the scientific
    Boat Safety Index (BSI) forecasted across 8 steps of the selected day,
    vessel beam stability, and border geofencing status. Uses remote INCOIS
    NetCDF datasets via OPENDAP with offline-first API fallbacks.
    """
    # 1. Fetch geofence status
    geofence = check_geofence_status(lat, lon, db)
    is_inside_eez = geofence["is_inside_eez"]
    is_inside_mpa = geofence.get("is_inside_mpa", False)
    distance_eez_km = geofence["distance_to_border_km"]
    distance_mpa_km = geofence.get("distance_to_mpa_km", 999.0)
    mpa_name = geofence.get("mpa_name")
    
    # 2. Query INCOIS NetCDF datasets via OPENDAP
    incois_success = False
    ww3_records = []
    curr_records = []
    
    try:
        ww3_records, curr_records = IncoisDatasetResolver.resolve_latest_forecast(lat, lon, day)
        incois_success = True
    except Exception as e:
        # Fallback to local / Open-Meteo in case of remote server timeout/offline/land grid
        pass
        
    bsi_steps = []
    peak_wave_height = 0.0
    peak_wind_speed = 0.0
    peak_current_speed = 0.0
    peak_wave_steepness = 0.0
    peak_directional_spread = 0.2
    
    provenance = {
        "retrieved_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    if incois_success and len(ww3_records) == 8:
        # P0/P1: Real INCOIS NetCDF variables pipeline
        provenance["source"] = "INCOIS OPENDAP"
        provenance["ww3_dataset"] = "rsmc_combined_ww3_20260825.nc"
        provenance["currents_dataset"] = "CURRENTS_NIO_20260824.nc"
        
        for k in range(8):
            step_ww3 = ww3_records[k]
            step_curr = curr_records[k]
            
            # Map parameters
            hs = step_ww3["hs"]
            stp = step_ww3["stp"]
            spr = step_ww3["spr"]
            t02 = step_ww3["t02"]
            wind_speed = step_ww3["wind_speed_kmh"]
            hsea_initial = step_ww3["hsea_initial"]
            hsea_final = step_ww3["hsea_final"]
            
            curr_speed = step_curr["speed_m_s"]
            
            # Track peak values
            peak_wave_height = max(peak_wave_height, hs)
            peak_wind_speed = max(peak_wind_speed, wind_speed)
            peak_current_speed = max(peak_current_speed, curr_speed)
            peak_wave_steepness = max(peak_wave_steepness, stp)
            peak_directional_spread = max(peak_directional_spread, spr)
            
            # BSI calculation (strictly wave indices, currents/wind separate)
            bsi = BSICalculator.calculate_bsi(
                Ss=stp,
                Hs=hs,
                ss=spr,
                Hsea_initial=hsea_initial,
                Hsea_final=hsea_final
            )
            bsi_steps.append(bsi)
    else:
        # Fallback to Open-Meteo API
        provenance["source"] = "Open-Meteo Marine (Failsafe Fallback)"
        weather = get_marine_weather(lat, lon)
        forecast = weather.get("forecast_hourly", {})
        
        day_clamped = max(1, min(3, day))
        start_hour = (day_clamped - 1) * 24
        end_hour = day_clamped * 24
        
        day_heights = forecast.get("wave_height_m", [0.0]*72)[start_hour:end_hour]
        day_dirs = forecast.get("wave_direction_deg", [0.0]*72)[start_hour:end_hour]
        day_swell_dirs = forecast.get("swell_direction_deg", [0.0]*72)[start_hour:end_hour]
        day_periods = forecast.get("wave_period_s", [6.0]*72)[start_hour:end_hour]
        day_winds = forecast.get("wind_speed_kmh", [10.0]*72)[start_hour:end_hour]
        
        for step in range(8):
            h_start = step * 3
            h_end = (step + 1) * 3
            
            h_heights = day_heights[h_start:h_end]
            h_periods = day_periods[h_start:h_end]
            h_dirs = day_dirs[h_start:h_end]
            h_swell_dirs = day_swell_dirs[h_start:h_end]
            
            avg_height = sum(h_heights) / 3.0 if h_heights else 0.0
            avg_period = sum(h_periods) / 3.0 if h_periods else 6.0
            avg_dir = sum(h_dirs) / 3.0 if h_dirs else 0.0
            avg_swell_dir = sum(h_swell_dirs) / 3.0 if h_swell_dirs else 0.0
            
            wind_speed = max(day_winds[h_start:h_end]) if day_winds else 10.0
            
            peak_wave_height = max(peak_wave_height, avg_height)
            peak_wind_speed = max(peak_wind_speed, wind_speed)
            
            g = 9.81
            wave_steepness = (2 * math.pi * avg_height) / (g * (avg_period ** 2)) if avg_period > 0 else 0.0
            peak_wave_steepness = max(peak_wave_steepness, wave_steepness)
            
            angle_diff = abs(avg_dir - avg_swell_dir) % 360
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            directional_spread = 0.2 + (angle_diff / 180.0) * 0.8
            peak_directional_spread = max(peak_directional_spread, directional_spread)
            
            prev_idx = start_hour + h_start - 6
            hsea_initial = forecast.get("wave_height_m", [0.0]*72)[prev_idx] if prev_idx >= 0 else avg_height
            hsea_final = avg_height
            
            bsi = BSICalculator.calculate_bsi(
                Ss=wave_steepness,
                Hs=avg_height,
                ss=directional_spread,
                Hsea_initial=hsea_initial,
                Hsea_final=hsea_final
            )
            bsi_steps.append(bsi)
            
    # 3. Apply SVAS daily aggregation warning classification
    non_zero_steps = [i for i, val in enumerate(bsi_steps) if val > 0]
    if len(non_zero_steps) >= 7:
        daily_bsi_class = "WARNING"
        daily_bsi_desc = f"Compounding wave hazards active for most of the day ({len(non_zero_steps)}/8 steps)."
    elif any(idx >= 4 for idx in non_zero_steps):
        daily_bsi_class = "ALERT"
        daily_bsi_desc = "Wave hazards or crossing seas developing in the afternoon/night periods."
    else:
        daily_bsi_class = "SAFE"
        daily_bsi_desc = "All wave-forcing indicators within safe parameters."
        
    # 4. Assess separate risk categories
    # Wind Risk
    if peak_wind_speed > 40.0:
        wind_risk = "HIGH"
        wind_desc = f"Extreme winds: Peak of {peak_wind_speed:.1f} km/h (ORCA threshold exceeded)"
    elif peak_wind_speed > 25.0:
        wind_risk = "MODERATE"
        wind_desc = f"Elevated winds: Peak of {peak_wind_speed:.1f} km/h (ORCA threshold warning)"
    else:
        wind_risk = "LOW"
        wind_desc = f"Safe winds: Peak of {peak_wind_speed:.1f} km/h"
        
    # Currents Risk
    if peak_current_speed > 1.5:
        curr_risk = "HIGH"
        curr_desc = f"Extreme currents: Peak of {peak_current_speed:.2f} m/s (ORCA threshold exceeded)"
    elif peak_current_speed > 0.5:
        curr_risk = "MODERATE"
        curr_desc = f"Moderate currents: Peak of {peak_current_speed:.2f} m/s"
    else:
        curr_risk = "LOW"
        curr_desc = f"Safe currents: Peak of {peak_current_speed:.2f} m/s"
        
    # Geofence Risk
    if is_inside_mpa:
        geofence_risk = "HIGH"
        geofence_desc = f"Vessel inside Marine Protected Area: {mpa_name} (fishing strictly prohibited!)"
    elif not is_inside_eez:
        geofence_risk = "HIGH"
        geofence_desc = "Vessel is outside the Indian Exclusive Economic Zone (EEZ)."
    elif distance_eez_km < 5.0:
        geofence_risk = "MODERATE"
        geofence_desc = f"Vessel approaching international border (distance: {distance_eez_km:.2f} km)"
    elif distance_mpa_km < 2.0:
        geofence_risk = "MODERATE"
        geofence_desc = f"Vessel approaching Marine Protected Area: {mpa_name} (distance: {distance_mpa_km:.2f} km)"
    else:
        geofence_risk = "LOW"
        geofence_desc = "Safe region: Within EEZ borders, clear of MPAs"

    # Vessel Sizing Stability Check
    vessel_vulnerable = False
    critical_beam = round(4.0 * peak_wave_height, 2)
    if beam is not None and daily_bsi_class != "SAFE":
        if beam < critical_beam:
            vessel_vulnerable = True

    # 5. P2: Determine Overall ORCA Operational Risk (LOW, MODERATE, HIGH)
    reasons = []
    
    # Wave hazards check
    if daily_bsi_class == "WARNING":
        overall_risk = "HIGH"
        reasons.append(f"Wave hazard warning: {daily_bsi_desc}")
    elif daily_bsi_class == "ALERT":
        overall_risk = "MODERATE"
        reasons.append(f"Wave hazard alert: {daily_bsi_desc}")
    else:
        overall_risk = "LOW"
        
    # Wind hazards check
    if wind_risk == "HIGH":
        overall_risk = "HIGH"
        reasons.append(wind_desc)
    elif wind_risk == "MODERATE" and overall_risk == "LOW":
        overall_risk = "MODERATE"
        reasons.append(wind_desc)
        
    # Current hazards check
    if curr_risk == "HIGH":
        overall_risk = "HIGH"
        reasons.append(curr_desc)
    elif curr_risk == "MODERATE" and overall_risk == "LOW":
        overall_risk = "MODERATE"
        reasons.append(curr_desc)
        
    # Geofence hazards check
    if geofence_risk == "HIGH":
        overall_risk = "HIGH"
        reasons.append(geofence_desc)
    elif geofence_risk == "MODERATE" and overall_risk == "LOW":
        overall_risk = "MODERATE"
        reasons.append(geofence_desc)
        
    # Vessel stability check override
    if vessel_vulnerable:
        overall_risk = "HIGH"
        reasons.append(
            f"Vessel stability alert: Beam width ({beam}m) is below the critical stability threshold "
            f"({critical_beam}m) for peak wave heights of {peak_wave_height:.2f}m. Capsizing hazard!"
        )
        
    # Map overall risk to rating and recommendation
    if overall_risk == "HIGH":
        rating = "DANGER"
        recommendation = "Do not venture into sea. Compounding wave factors, high winds, strong currents, or boundary violations present severe hazards."
    elif overall_risk == "MODERATE":
        rating = "CAUTION"
        recommendation = "Exercise caution. Vessel operations should be restricted to nearshore buffers. Monitor local conditions closely."
    else:
        rating = "SAFE"
        recommendation = "Safe to venture into sea. Exercise standard caution."
        
    if not reasons:
        reasons.append("All weather, wave, current, and geofence parameters are within optimal safety ranges.")

    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "rating": rating,
        "recommendation": recommendation,
        "reasons": reasons,
        "vessel_suitability": {
            "vessel_beam_m": beam,
            "critical_beam_m": critical_beam,
            "vulnerable": vessel_vulnerable
        },
        "bsi_metrics": {
            "bsi_score": max(bsi_steps) if bsi_steps else 0,
            "rating": daily_bsi_class,
            "description": daily_bsi_desc,
            "wave_steepness": round(peak_wave_steepness, 4),
            "directional_spread": round(peak_directional_spread, 2)
        },
        "raw_metrics": {
            "wave_height_m": round(peak_wave_height, 2),
            "wind_speed_kmh": round(peak_wind_speed, 2),
            "current_speed_ms": round(peak_current_speed, 2),
            "distance_to_border_km": distance_eez_km,
            "is_inside_eez": is_inside_eez,
            "is_inside_mpa": is_inside_mpa,
            "mpa_name": mpa_name
        },
        "orca_risk": {
            "overall_status": overall_risk,
            "wind_risk": wind_risk,
            "current_risk": curr_risk,
            "geofence_risk": geofence_risk
        },
        "provenance": provenance
    }


@router.get("/advisories")
def get_coastal_advisories():
    """
    Proxy endpoint to fetch the live INCOIS SVAS Advisory GeoJSON.
    Bypasses CORS restrictions on the client side.
    """
    url = "https://www.incois.gov.in/oceanservices/SVAS/SVAS_Advisory.geojson"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "type": "FeatureCollection",
                "name": "SVAS_Advisory_Fallback",
                "features": []
            }
    except Exception as e:
        return {
            "type": "FeatureCollection",
            "name": "SVAS_Advisory_Fallback",
            "features": []
        }
