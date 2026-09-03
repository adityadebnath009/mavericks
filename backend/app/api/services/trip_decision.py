import logging
from datetime import datetime
from shapely.geometry import Point, shape
from shapely.ops import nearest_points
from sqlalchemy.orm import Session

from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.pfz_routing import PFZRoutingService
from app.api.endpoints.geofence import evaluate_geofence_offline
from app.core.exceptions import DataUnavailableError
from app.core.enums import TripDecision

logger = logging.getLogger(__name__)

class TripDecisionEngine:
    @classmethod
    def analyze_trip(
        cls,
        start_lat: float,
        start_lon: float,
        departure_time: str,
        beam_m: float,
        length_m: float,
        cruising_speed_kn: float,
        db: Session
    ) -> dict:
        return cls._analyze_trip_internal(
            start_lat, start_lon, departure_time, beam_m, length_m, cruising_speed_kn, db
        )

    @classmethod
    def _analyze_trip_internal(
        cls,
        start_lat: float,
        start_lon: float,
        departure_time: str,
        beam_m: float,
        length_m: float,
        cruising_speed_kn: float,
        db: Session
    ) -> dict:
        # 1. Fetch active PFZ contour candidates from WFS
        try:
            pfz_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        except Exception as e:
            logger.error(f"Error fetching WFS contours: {e}")
            raise DataUnavailableError("PFZ advisory WFS service is currently offline or unreachable.")

        features = pfz_geojson.get("features", [])
        if not features:
            raise DataUnavailableError("No active INCOIS PFZ Advisory zones found in coastal waters.")

        evaluated_candidates = []
        approved_trips = []

        # 2. Evaluate each PFZ target
        for feat in features:
            pfz_id = feat.get("id", "unknown_pfz")
            geom_shape = shape(feat["geometry"])
            vessel_pt = Point(start_lon, start_lat)
            nearest_geom_pt, _ = nearest_points(geom_shape, vessel_pt)
            nearest_lat = nearest_geom_pt.y
            nearest_lon = nearest_geom_pt.x

            # Geofence target check
            try:
                gf = evaluate_geofence_offline(nearest_lat, nearest_lon)
                if gf.get("is_inside_mpa"):
                    evaluated_candidates.append({
                        "pfz_id": pfz_id,
                        "status": "REJECTED",
                        "reason": f"Target is in Marine Protected Area: {gf.get('mpa_name')}"
                    })
                    continue
                if not gf.get("is_inside_eez"):
                    evaluated_candidates.append({
                        "pfz_id": pfz_id,
                        "status": "REJECTED",
                        "reason": "Target is outside Indian EEZ."
                    })
                    continue
            except Exception as e:
                evaluated_candidates.append({
                    "pfz_id": pfz_id,
                    "status": "REJECTED",
                    "reason": "Geofence offline."
                })
                continue

            # Route calculation
            try:
                route_res = PFZRoutingService.calculate_optimal_route(
                    start_lat=start_lat,
                    start_lon=start_lon,
                    end_lat=nearest_lat,
                    end_lon=nearest_lon,
                    beam_m=beam_m,
                    cruising_speed_kn=cruising_speed_kn,
                    departure_time=departure_time
                )
            except DataUnavailableError as e:
                evaluated_candidates.append({
                    "pfz_id": pfz_id,
                    "status": TripDecision.DATA_UNAVAILABLE.value,
                    "reason": str(e)
                })
                continue
            except Exception as e:
                logger.error(f"Routing failed to PFZ {pfz_id}: {e}")
                evaluated_candidates.append({
                    "pfz_id": pfz_id,
                    "status": "REJECTED",
                    "reason": "Internal routing failure."
                })
                continue

            if route_res.get("decision") == "REJECTED_NO_SAFE_ROUTE":
                evaluated_candidates.append({
                    "pfz_id": pfz_id,
                    "status": "REJECTED",
                    "reason": "No path satisfies capsize safety thresholds."
                })
                continue

            # Approvals
            snapshots = route_res.get("snapshots", [])
            max_bsi = max((s["bsi"] for s in snapshots), default=0) if snapshots else 0
            
            travel_time_hours = 0.0
            if len(snapshots) >= 2:
                dt_start = datetime.fromisoformat(snapshots[0]["time"])
                dt_end = datetime.fromisoformat(snapshots[-1]["time"])
                travel_time_hours = (dt_end - dt_start).total_seconds() / 3600.0

            approved_trips.append({
                "pfz_id": pfz_id,
                "status": "RECOMMENDED" if max_bsi < 2 else "CAUTION",
                "travel_time_hours": travel_time_hours,
                "route_coords": route_res["route_coords"],
                "snapshots": snapshots,
                "segments": route_res.get("segments", []),
                "max_bsi": max_bsi
            })

        approved_trips.sort(key=lambda t: (0 if t["status"] == "RECOMMENDED" else 1, t["travel_time_hours"]))

        if approved_trips:
            top_trip = approved_trips[0]
            other_approved = [
                {
                    "pfz_id": t["pfz_id"],
                    "status": t["status"],
                    "reason": f"Safe option. Travel Time: {t['travel_time_hours']:.1f} hrs."
                }
                for t in approved_trips[1:]
            ]
            alternatives = other_approved + evaluated_candidates

            return {
                "decision": top_trip["status"],
                "recommended_pfz": {
                    "id": top_trip["pfz_id"],
                    "travel_time_hours": round(top_trip["travel_time_hours"], 2),
                    "route_coords": top_trip["route_coords"],
                    "snapshots": top_trip["snapshots"],
                    "segments": top_trip["segments"]
                },
                "decision_reasons": [
                    {"factor": "Safety", "detail": f"Max BSI across route: {top_trip['max_bsi']}"}
                ],
                "alternatives": alternatives
            }
        else:
            return {
                "decision": TripDecision.REJECTED_NO_SAFE_ROUTE.value,
                "reason": "All PFZ zones are inaccessible or carry excessive weather risk.",
                "alternatives": evaluated_candidates
            }
