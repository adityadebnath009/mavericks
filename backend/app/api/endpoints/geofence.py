import json
import os
from app.db.session import get_db
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.exceptions import DataUnavailableError

try:
    from shapely.geometry import Point, shape
except ImportError:
    shape = None
    Point = None

router = APIRouter()
db_dependency = Depends(get_db)


_cached_geojson = None
_cached_geometries = []

def load_fallback_geojson():
    """
    Loads static boundaries GeoJSON dataset for offline-first resilience.
    Caches the file I/O and parsed shapely geometries for blazing fast repeated lookups.
    """
    global _cached_geojson, _cached_geometries
    if _cached_geojson is not None:
        return _cached_geojson
        
    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/boundaries/boundaries_fallback.geojson")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/boundaries/boundaries_fallback.geojson")),
        os.path.abspath("data/boundaries/boundaries_fallback.geojson")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _cached_geojson = json.load(f)
                    if Point and shape and _cached_geojson.get("features"):
                        for feat in _cached_geojson.get("features", []):
                            geom_data = feat.get("geometry")
                            if geom_data:
                                _cached_geometries.append({
                                    "geom": shape(geom_data),
                                    "type": feat.get("properties", {}).get("type"),
                                    "name": feat.get("properties", {}).get("name")
                                })
                    return _cached_geojson
            except Exception:
                continue
                
    _cached_geojson = {"type": "FeatureCollection", "features": []}
    return _cached_geojson


def evaluate_geofence_offline(lat: float, lon: float):
    """
    Evaluates vessel point coordinates against offline boundary GeoJSON features
    using Shapely geometry calculations.
    """
    fallback_data = load_fallback_geojson()
    is_inside_eez = False
    distance_eez = 999.0
    is_inside_mpa = False
    distance_mpa = 999.0
    mpa_name = None

    if Point and shape and _cached_geometries:
        pt = Point(lon, lat)
        for feat in _cached_geometries:
            geom = feat["geom"]
            f_type = feat["type"]
            f_name = feat["name"]

            if f_type == "EEZ":
                if geom.contains(pt):
                    is_inside_eez = True
                try:
                    dist_deg = geom.boundary.distance(pt)
                    dist_km = dist_deg * 111.0
                    if dist_km < distance_eez:
                        distance_eez = dist_km
                except Exception:
                    pass
            elif f_type == "MPA":
                if geom.contains(pt):
                    is_inside_mpa = True
                    mpa_name = f_name
                try:
                    dist_deg = geom.distance(pt)
                    dist_km = dist_deg * 111.0
                    if dist_km < distance_mpa:
                        distance_mpa = dist_km
                except Exception:
                    pass
    else:
        raise DataUnavailableError("Geofence data is missing or malformed.")

    if is_inside_mpa:
        status = "DANGER_INSIDE_RESTRICTED_ZONE"
        message = f"Vessel is inside Marine Protected Area: {mpa_name}! Fishing is strictly prohibited."
    elif not is_inside_eez:
        status = "DANGER_OUTSIDE_BORDER"
        message = "Vessel has crossed international maritime boundaries!"
    elif distance_eez < 5.0:
        status = "WARNING_APPROACHING_BORDER"
        message = f"Vessel is approaching international border. Distance: {distance_eez:.2f} km."
    elif distance_mpa < 2.0:
        status = "WARNING_APPROACHING_RESTRICTED_ZONE"
        message = f"Vessel is approaching Marine Protected Area: {mpa_name} (distance: {distance_mpa:.2f} km)."
    else:
        status = "SAFE_INSIDE_BORDER"
        message = "Vessel is safely inside Indian maritime territories."

    return {
        "coordinates": {"latitude": lat, "longitude": lon},
        "is_inside_eez": is_inside_eez,
        "distance_to_border_km": round(distance_eez, 3),
        "is_inside_mpa": is_inside_mpa,
        "distance_to_mpa_km": round(distance_mpa, 3),
        "mpa_name": mpa_name,
        "status": status,
        "message": message,
    }


@router.get("")
@router.get("/")
def check_geofence_status(
    lat: float = Query(..., description="Latitude of the vessel"),
    lon: float = Query(..., description="Longitude of the vessel"),
    db: Session = db_dependency,
):
    """
    Checks if a given coordinate lies within the Indian Exclusive Economic Zone (EEZ)
    and calculates the shortest distance (in kilometers) to the nearest boundary.
    Falls back gracefully to offline boundaries GeoJSON if database is unreachable.
    """
    try:
        # 1. PostGIS Query for EEZ Boundaries
        query_eez = text("""
                SELECT 
                    bool_or(ST_Contains(geometry, ST_SetSRID(ST_Point(:lon, :lat), 4326))) AS is_inside,
                    min(ST_Distance(
                        ST_Boundary(geometry)::geography, 
                        ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography
                    )) / 1000.0 AS distance_km
                FROM india_eez;
            """)

        # 2. PostGIS Query for Marine Protected Areas (MPAs)
        query_mpa = text("""
                SELECT 
                    bool_or(ST_Contains(geometry, ST_SetSRID(ST_Point(:lon, :lat), 4326))) AS is_inside,
                    min(ST_Distance(
                        geometry::geography, 
                        ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography
                    )) / 1000.0 AS distance_km,
                    (
                        SELECT "NAME_ENG" 
                        FROM marine_protected_areas 
                        WHERE ST_Contains(geometry, ST_SetSRID(ST_Point(:lon, :lat), 4326)) 
                        LIMIT 1
                    ) AS mpa_name
                FROM marine_protected_areas;
            """)

        res_eez = db.execute(query_eez, {"lon": lon, "lat": lat}).fetchone()
        res_mpa = db.execute(query_mpa, {"lon": lon, "lat": lat}).fetchone()

        # Extract EEZ spatial details
        is_inside_eez = (
            bool(res_eez.is_inside)
            if res_eez and res_eez.is_inside is not None
            else False
        )
        distance_eez = (
            float(res_eez.distance_km)
            if res_eez and res_eez.distance_km is not None
            else 999.0
        )

        # Extract MPA spatial details
        is_inside_mpa = (
            bool(res_mpa.is_inside)
            if res_mpa and res_mpa.is_inside is not None
            else False
        )
        distance_mpa = (
            float(res_mpa.distance_km)
            if res_mpa and res_mpa.distance_km is not None
            else 999.0
        )
        mpa_name = res_mpa.mpa_name if res_mpa and res_mpa.mpa_name else None

        # 3. Determine safety warning state based on spatial thresholds
        if is_inside_mpa:
            status = "DANGER_INSIDE_RESTRICTED_ZONE"
            message = f"Vessel is inside Marine Protected Area: {mpa_name}! Fishing is strictly prohibited."
        elif not is_inside_eez:
            status = "DANGER_OUTSIDE_BORDER"
            message = "Vessel has crossed international maritime boundaries!"
        elif distance_eez < 5.0:
            status = "WARNING_APPROACHING_BORDER"
            message = f"Vessel is approaching international border. Distance: {distance_eez:.2f} km."
        elif distance_mpa < 2.0:
            status = "WARNING_APPROACHING_RESTRICTED_ZONE"
            message = f"Vessel is approaching Marine Protected Area: {mpa_name} (distance: {distance_mpa:.2f} km)."
        else:
            status = "SAFE_INSIDE_BORDER"
            message = "Vessel is safely inside Indian maritime territories."

        return {
            "coordinates": {"latitude": lat, "longitude": lon},
            "is_inside_eez": is_inside_eez,
            "distance_to_border_km": round(distance_eez, 3),
            "is_inside_mpa": is_inside_mpa,
            "distance_to_mpa_km": round(distance_mpa, 3),
            "mpa_name": mpa_name,
            "status": status,
            "message": message,
        }
    except Exception:
        # Fallback to offline Shapely calculation from GeoJSON boundaries
        return evaluate_geofence_offline(lat, lon)


_cached_geofence_geojson = None

@router.get("/geojson")
@router.get("/geojson/")
def get_geofence_geojson(db: Session = db_dependency):
    global _cached_geofence_geojson
    if _cached_geofence_geojson is not None:
        return _cached_geofence_geojson
    
    fallback = load_fallback_geojson()
    if fallback:
        _cached_geofence_geojson = fallback
        return fallback
        
    return {"type": "FeatureCollection", "features": []}

