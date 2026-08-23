from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.db.models import Vessel
from app.api.endpoints.geofence import check_geofence_status

router = APIRouter()

@router.post("/{vessel_id}/ping")
def ping_vessel_location(
    vessel_id: int,
    lat: float = Query(..., description="Vessel current latitude"),
    lon: float = Query(..., description="Vessel current longitude"),
    db: Session = Depends(get_db)
):
    """
    Updates the vessel's coordinate in the database (active tracking)
    and returns its current geofence boundary warning status.
    """
    # 1. Fetch the vessel from the database
    vessel = db.query(Vessel).filter(Vessel.id == vessel_id, Vessel.is_active == True).first()
    if not vessel:
        raise HTTPException(
            status_code=404, 
            detail=f"Active vessel with ID {vessel_id} not registered."
        )
        
    # 2. Update coordinates in database
    vessel.last_latitude = lat
    vessel.last_longitude = lon
    db.commit()
    
    # 3. Check current geofence status dynamically
    geofence_status = check_geofence_status(lat, lon, db)
    
    return {
        "vessel": {
            "id": vessel.id,
            "name": vessel.name,
            "registration": vessel.registration_number
        },
        "last_coordinates": {"latitude": lat, "longitude": lon},
        "boundary_alert": {
            "status": geofence_status["status"],
            "distance_to_border_km": geofence_status["distance_to_border_km"],
            "message": geofence_status["message"]
        }
    }
