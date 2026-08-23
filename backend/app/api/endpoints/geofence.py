from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()

@router.get("/")
def check_geofence_status(
    lat: float = Query(..., description="Latitude of the vessel"),
    lon: float = Query(..., description="Longitude of the vessel"),
    db: Session = Depends(get_db)
):
    """
    Checks if a given coordinate lies within the Indian Exclusive Economic Zone (EEZ)
    and calculates the shortest distance (in kilometers) to the nearest boundary.
    """
    try:
        # PostGIS Query:
        # - ST_Contains: checks if the vessel coordinate lies inside the India EEZ polygon
        # - ST_Distance: calculates geodesic distance from coordinate to nearest boundary edge
        # - geometry::geography cast converts flat coordinates to meters (divided by 1000 for km)
        query = text("""
            SELECT 
                bool_or(ST_Contains(geometry, ST_SetSRID(ST_Point(:lon, :lat), 4326))) AS is_inside,
                min(ST_Distance(
                    ST_Boundary(geometry)::geography, 
                    ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography
                )) / 1000.0 AS distance_km
            FROM india_eez;
        """)
        
        result = db.execute(query, {"lon": lon, "lat": lat}).fetchone()
        
        if not result:
            # If the database table is empty or query fails to match
            raise HTTPException(
                status_code=404, 
                detail="India EEZ boundary data not found in database. Run seed.py first."
            )
            
        is_inside = bool(result.is_inside)
        distance_km = float(result.distance_km)
        
        # Determine safety warning state based on buffer zones
        if not is_inside:
            status = "DANGER_OUTSIDE_BORDER"
            message = "Vessel has crossed international maritime boundaries!"
        elif distance_km < 5.0:
            status = "WARNING_APPROACHING_BORDER"
            message = f"Vessel is approaching border. Current distance: {distance_km:.2f} km."
        else:
            status = "SAFE_INSIDE_BORDER"
            message = "Vessel is safely inside Indian maritime territories."
            
        return {
            "coordinates": {"latitude": lat, "longitude": lon},
            "is_inside_eez": is_inside,
            "distance_to_border_km": round(distance_km, 3),
            "status": status,
            "message": message
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database spatial query error: {e}"
        )
