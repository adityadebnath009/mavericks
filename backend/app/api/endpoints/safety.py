from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.endpoints.weather import get_marine_weather
from app.api.endpoints.geofence import check_geofence_status

router = APIRouter()

@router.get("/")
def get_safety_assessment(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    db: Session = Depends(get_db)
):
    """
    Computes a unified Marine Safety Score (0-100) by combining real-time
    meteorological data and territorial boundary geofence checks.
    """
    # 1. Fetch weather and geofence data
    weather = get_marine_weather(lat, lon)
    geofence = check_geofence_status(lat, lon, db)
    
    # 2. Extract values
    wave_height = weather["sea_state"]["wave_height_m"]
    wind_speed_kmh = weather["wind"]["speed_kmh"]
    is_inside = geofence["is_inside_eez"]
    distance_km = geofence["distance_to_border_km"]
    
    # 3. Calculate Safety Deductions (Rule-Based Math)
    deductions = {}
    reasons = []
    
    # Wave height checks (Deductions out of 40)
    # Safe: <1.5m, Caution: 1.5m-2.5m, Danger: >2.5m
    if wave_height is not None:
        if wave_height > 2.5:
            deductions["waves"] = 40
            reasons.append(f"Dangerous sea state: Wave heights of {wave_height:.2f}m exceed safe limits (>2.5m).")
        elif wave_height > 1.5:
            deductions["waves"] = 20
            reasons.append(f"Cautionary sea state: Moderate wave heights of {wave_height:.2f}m.")
        else:
            deductions["waves"] = 0
            
    # Wind speed checks (Deductions out of 30)
    # Safe: <25 kmh (approx 13.5 kt), Caution: 25-40 kmh (13.5-22 kt), Danger: >40 kmh (>22 kt)
    if wind_speed_kmh is not None:
        if wind_speed_kmh > 40:
            deductions["wind"] = 30
            reasons.append(f"Gale warning: Extreme wind speed of {wind_speed_kmh:.1f} km/h.")
        elif wind_speed_kmh > 25:
            deductions["wind"] = 15
            reasons.append(f"Cautionary winds: Fresh breeze speed of {wind_speed_kmh:.1f} km/h.")
        else:
            deductions["wind"] = 0
            
    # Geofence boundary checks (Deductions out of 30)
    if not is_inside:
        deductions["boundary"] = 30
        reasons.append("Vessel is outside Indian territorial waters. High risk of detention.")
    elif distance_km < 5.0:
        deductions["boundary"] = 15
        reasons.append(f"Vessel is approaching international maritime border (distance: {distance_km:.2f} km).")
    else:
        deductions["boundary"] = 0
        
    # Calculate total score
    total_deduction = sum(deductions.values())
    safety_score = max(0, 100 - total_deduction)
    
    # 4. Determine overall rating
    if safety_score >= 80:
        rating = "SAFE"
        recommendation = "Safe to venture into sea. Exercise standard caution."
    elif safety_score >= 50:
        rating = "CAUTION"
        recommendation = "Exercise caution. Coastal fishing is safe, but avoid deep-sea operations or areas near the border."
    else:
        rating = "DANGER"
        recommendation = "Do not venture into sea. High waves, strong winds, or border violations present critical hazards."
        
    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "safety_score": safety_score,
        "rating": rating,
        "recommendation": recommendation,
        "reasons": reasons if reasons else ["Weather and boundary parameters are within optimal safety ranges."],
        "metrics": {
            "wave_height_m": wave_height,
            "wind_speed_kmh": wind_speed_kmh,
            "distance_to_border_km": distance_km,
            "is_inside_eez": is_inside
        }
    }
