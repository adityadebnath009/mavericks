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


def load_fallback_geojson():
    """
    Loads static boundaries GeoJSON dataset for offline-first resilience.
    """
    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/boundaries/boundaries_fallback.geojson")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/boundaries/boundaries_fallback.geojson")),
        os.path.abspath("data/boundaries/boundaries_fallback.geojson")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return {"type": "FeatureCollection", "features": []}


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

    if Point and shape and fallback_data.get("features"):
        pt = Point(lon, lat)
        for feat in fallback_data.get("features", []):
            geom_data = feat.get("geometry")
            if not geom_data:
                continue
            geom = shape(geom_data)
            f_type = feat.get("properties", {}).get("type")
            f_name = feat.get("properties", {}).get("name")

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
    """
    Fetches simplified geometries of the Indian EEZ boundary and Marine Protected Areas (MPAs)
    in GeoJSON format to render directly on the interactive map.
    Falls back to 'data/boundaries/boundaries_fallback.geojson' if remote database is unreachable.
    """
    global _cached_geofence_geojson
    if _cached_geofence_geojson is not None:
        return _cached_geofence_geojson

    try:
        # 1. Fetch simplified EEZ boundary
        query_eez = text("""
            SELECT ST_AsGeoJSON(ST_Simplify(geometry, 0.01)) as geojson
            FROM india_eez;
        """)
        # 2. Fetch simplified Marine Protected Areas (MPAs)
        query_mpa = text("""
            SELECT "NAME_ENG" as name, ST_AsGeoJSON(ST_Simplify(geometry, 0.005)) as geojson
            FROM marine_protected_areas;
        """)

        eez_rows = db.execute(query_eez).fetchall()
        mpa_rows = db.execute(query_mpa).fetchall()

        features = []

        # Parse EEZ Boundaries
        for row in eez_rows:
            if row.geojson:
                geom = json.loads(row.geojson)
                features.append({
                    "type": "Feature",
                    "properties": {
                        "type": "EEZ",
                        "name": "Indian Exclusive Economic Zone (EEZ)"
                    },
                    "geometry": geom
                })

        # Parse MPA Restricted Zones
        for row in mpa_rows:
            if row.geojson:
                geom = json.loads(row.geojson)
                features.append({
                    "type": "Feature",
                    "properties": {
                        "type": "MPA",
                        "name": row.name or "Marine Protected Area"
                    },
                    "geometry": geom
                })

        if features:
            _cached_geofence_geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            return _cached_geofence_geojson
        # Fallback if table was empty
        return load_fallback_geojson()
    except Exception:
        # Return fallback boundaries GeoJSON dataset if DB connection drops
        return load_fallback_geojson()

