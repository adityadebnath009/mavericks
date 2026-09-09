"""Read-only adapter for the existing local INCOIS PFZ cache."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable


class PFZCacheProvider:
    _path = Path(__file__).resolve().parents[3] / "data/cache/pfz_lines_augmented_v3.json"

    @staticmethod
    def _points(geometry: Dict[str, Any]) -> Iterable[tuple[float, float]]:
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") == "LineString":
            yield from ((float(lon), float(lat)) for lon, lat in coordinates)
        elif geometry.get("type") == "MultiLineString":
            for line in coordinates:
                yield from ((float(lon), float(lat)) for lon, lat in line)

    @staticmethod
    def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius = 6371.0
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def nearest(self, lat: float, lon: float, max_age_hours: float = 24) -> Dict[str, Any]:
        if not self._path.exists():
            return {"source": "incois_pfz_cache", "state": "UNAVAILABLE", "reason": "Local PFZ cache is absent."}
        try:
            data = json.loads(self._path.read_text())
            stamp = data.get("timeStamp")
            observed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else datetime.fromtimestamp(self._path.stat().st_mtime, tz=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - observed).total_seconds() / 3600
            state = "CACHED" if age_hours <= max_age_hours else "STALE"
            closest = None
            for feature in data.get("features", []):
                for point_lon, point_lat in self._points(feature.get("geometry", {})):
                    distance = self._distance_km(lat, lon, point_lat, point_lon)
                    if closest is None or distance < closest[0]:
                        closest = (distance, point_lat, point_lon, feature)
            if closest is None:
                return {"source": "incois_pfz_cache", "state": "UNAVAILABLE", "reason": "PFZ cache contains no usable geometry."}
            distance, point_lat, point_lon, feature = closest
            return {"source": "incois_pfz_cache", "state": state, "fetchedAt": observed.isoformat(), "ageHours": round(age_hours, 2),
                    "point": {"lat": point_lat, "lon": point_lon}, "distanceKm": round(distance, 2),
                    "properties": feature.get("properties", {}), "feature": feature}
        except Exception as exc:
            return {"source": "incois_pfz_cache", "state": "UNAVAILABLE", "reason": str(exc)}
