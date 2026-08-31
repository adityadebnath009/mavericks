import json
import os
import math
from fastapi import APIRouter, HTTPException

router = APIRouter()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("/nearby")
def get_nearby_landing_centers(lat: float, lon: float, limit: int = 5):
    """
    Returns the nearest official INCOIS landing centers to a given coordinate.
    """
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        lc_file = os.path.join(base_dir, "data/landing_centers.json")
        
        with open(lc_file, "r") as f:
            data = json.load(f)
            
        centers = []
        for feature in data.get("features", []):
            coords = feature["geometry"]["coordinates"]
            # GeoJSON points are [lon, lat]
            c_lon, c_lat = coords[0], coords[1]
            dist = haversine(lat, lon, c_lat, c_lon)
            
            props = feature.get("properties", {})
            centers.append({
                "id": props.get("LC_UNIQUE_") or props.get("OBJECTID"),
                "name": props.get("LC_NAME", "Unknown"),
                "district": props.get("DIST_NAME", "Unknown"),
                "sector": props.get("SECTOR_NAM", "Unknown"),
                "lat": c_lat,
                "lon": c_lon,
                "distance_km": round(dist, 2)
            })
            
        # Sort by distance and slice
        centers.sort(key=lambda x: x["distance_km"])
        return {"status": "success", "landing_centers": centers[:limit]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
