import math
import os
import json
from dataclasses import dataclass, field
from typing import List, Optional

import psycopg2

# ---------------------------------------------------------------------------
# Configuration — override via environment variables
# ---------------------------------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "orca"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", ""),
}

BORDER_WARNING_KM = float(os.getenv("BORDER_WARNING_KM", "5"))
MPA_WARNING_KM = float(os.getenv("MPA_WARNING_KM", "2"))


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

@dataclass
class MPAResult:
    name: str
    category: Optional[str]
    inside: bool
    distance_km: float


@dataclass
class GeospatialAssessment:
    latitude: float
    longitude: float
    in_india_eez: bool
    distance_to_eez_boundary_km: float
    border_warning: bool
    nearby_mpas: List[MPAResult] = field(default_factory=list)
    mpa_warning: bool = False

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "in_india_eez": self.in_india_eez,
            "distance_to_eez_boundary_km": round(self.distance_to_eez_boundary_km, 2),
            "border_warning": self.border_warning,
            "nearby_mpas": [
                {
                    "name": m.name,
                    "category": m.category,
                    "inside": m.inside,
                    "distance_km": round(m.distance_km, 2),
                }
                for m in self.nearby_mpas
            ],
            "mpa_warning": self.mpa_warning,
        }


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class GeospatialReasoningService:
    """
    Static-method service, called directly on the class — matching
    the pattern used by PFZEnricherService.enrich_point(lat, lon):

        GeospatialReasoningService.analyze(lat, lon)
    """

    @staticmethod
    def _connect():
        return psycopg2.connect(**DB_CONFIG)

    @staticmethod
    def _validate_coordinates(lat, lon) -> None:
        if not isinstance(lat, (int, float)) or isinstance(lat, bool):
            raise TypeError(f"latitude must be a number, got {type(lat).__name__}")
        if not isinstance(lon, (int, float)) or isinstance(lon, bool):
            raise TypeError(f"longitude must be a number, got {type(lon).__name__}")
        if not math.isfinite(lat) or not math.isfinite(lon):
            raise ValueError(
                f"Coordinates out of bounds: latitude={lat}, longitude={lon} (non-finite)"
            )
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude out of bounds: {lat} (must be between -90 and 90)")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude out of bounds: {lon} (must be between -180 and 180)")

    @classmethod
    def analyze(cls, lat: float, lon: float) -> dict:
        """
        Entry point for the Planner. Synchronous, matching the rest of
        the service layer. Raises TypeError for non-numeric input and
        ValueError for out-of-range/non-finite coordinates.
        """
        cls._validate_coordinates(lat, lon)

        with cls._connect() as conn:
            in_eez, dist_to_boundary_m = cls._check_eez(conn, lat, lon)
            mpas = cls._check_mpas(conn, lat, lon)

        dist_to_boundary_km = dist_to_boundary_m / 1000.0
        border_warning = (not in_eez) or (dist_to_boundary_km <= BORDER_WARNING_KM)
        mpa_warning = any(m.inside or m.distance_km <= MPA_WARNING_KM for m in mpas)

        result = GeospatialAssessment(
            latitude=lat,
            longitude=lon,
            in_india_eez=in_eez,
            distance_to_eez_boundary_km=dist_to_boundary_km,
            border_warning=border_warning,
            nearby_mpas=mpas,
            mpa_warning=mpa_warning,
        )
        return result.to_dict()

    @staticmethod
    def _check_eez(conn, lat: float, lon: float):
        """Returns (is_inside: bool, distance_to_boundary_metres: float)."""
        query = """
            SELECT
                ST_Contains(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS inside,
                ST_Distance(
                    ST_Boundary(geom)::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS dist_m
            FROM india_eez
            ORDER BY dist_m ASC
            LIMIT 1;
        """
        with conn.cursor() as cur:
            cur.execute(query, (lon, lat, lon, lat))
            row = cur.fetchone()
            if row is None:
                return False, 0.0
            return bool(row[0]), float(row[1])

    @staticmethod
    def _check_mpas(conn, lat: float, lon: float, limit: int = 5) -> List[MPAResult]:
        """Returns the nearest MPAs (inside or nearby), closest first."""
        query = """
            SELECT
                name,
                category,
                ST_Contains(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS inside,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS dist_m
            FROM marine_protected_areas
            ORDER BY dist_m ASC
            LIMIT %s;
        """
        with conn.cursor() as cur:
            cur.execute(query, (lon, lat, lon, lat, limit))
            rows = cur.fetchall()

        return [
            MPAResult(name=r[0], category=r[1], inside=bool(r[2]), distance_km=float(r[3]) / 1000.0)
            for r in rows
        ]


# ---------------------------------------------------------------------------
# Quick manual test — run `python geospatial_agent.py`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example position: near Puri Beach, Odisha (from the SIH problem example)
    result = GeospatialReasoningService.analyze(19.8, 85.85)
    print(json.dumps(result, indent=2))
