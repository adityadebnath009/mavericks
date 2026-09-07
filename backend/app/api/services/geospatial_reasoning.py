import json
import logging
from shapely.geometry import Point, shape
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)

# Using the pre-cached GeoJSON data directly
def evaluate_geofence_offline(lat: float, lon: float):
    # Simulated loading of cached bounding boxes to prevent PostGIS timeout
    is_safe = True
    alerts = []
    
    # 1. MPA (Marine Protected Area) Mock Check
    # (In production, this iterates over the parsed .geojson polygons using shapely)
    mpa_bounds = {"lat_min": 14.5, "lat_max": 15.5, "lon_min": 85.5, "lon_max": 86.5}
    if mpa_bounds["lat_min"] <= lat <= mpa_bounds["lat_max"] and mpa_bounds["lon_min"] <= lon <= mpa_bounds["lon_max"]:
        is_safe = False
        alerts.append("Vessel is inside or near a Marine Protected Area (MPA).")
        
    return {
        "geofence_status": "SAFE" if is_safe else "RESTRICTED",
        "geofence_alerts": alerts
    }

def compute_safe_route(start_lat: float, start_lon: float, target_lat: float, target_lon: float):
    """
    Computes an optimal path (A*) avoiding restricted zones.
    Returns a mocked path for demonstration.
    """
    path = [
        {"lat": start_lat, "lon": start_lon},
        {"lat": (start_lat + target_lat) / 2.0, "lon": (start_lon + target_lon) / 2.0 + 0.1}, # curved avoiding direct path
        {"lat": target_lat, "lon": target_lon}
    ]
    
    # Calculate travel time based on 10 knots average speed
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [start_lat, start_lon, target_lat, target_lon])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_km = R * c
    
    travel_time_hours = distance_km / 18.52 # 10 knots in km/h
    
    return {
        "route_path": path,
        "travel_time": round(travel_time_hours, 2),
        "estimated_arrival_time": f"T+{round(travel_time_hours, 2)}h"
    }
