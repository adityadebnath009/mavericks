import math
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile

logger = logging.getLogger("route_bsi_profiler")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

class RouteBsiProfiler:
    """
    v2.3: Route Intelligence & ETA Engine.
    Evaluates spatial-temporal BSI across a route and optimizes departure times.
    """
    
    def __init__(self, marine_forecast_service, bsi_engine: OrcaBsiEngine):
        self.marine_service = marine_forecast_service
        self.bsi_engine = bsi_engine

    def compute_etas(self, route_coords: List[Dict[str, float]], vessel: VesselProfile, departure_time: datetime) -> List[Dict]:
        """
        v2.3-A: Route sampling & ETA calculation.
        """
        if not route_coords:
            return []
            
        if vessel.cruising_speed_kn <= 0:
            raise ValueError("Vessel cruising speed must be strictly positive.")
        speed_kmh = vessel.cruising_speed_kn * 1.852
        max_hull_speed = max(30.0, 2.5 * math.sqrt(vessel.length_m))
        speed_kmh = min(speed_kmh, max_hull_speed)
            
        profile = []
        current_time = departure_time
        
        # Node 0 (Departure)
        profile.append({
            "node_idx": 0,
            "lat": route_coords[0]["lat"],
            "lon": route_coords[0]["lon"],
            "eta": current_time,
            "distance_from_prev_km": 0.0
        })
        
        for i in range(1, len(route_coords)):
            prev = route_coords[i-1]
            curr = route_coords[i]
            
            dist_km = haversine_distance(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
            hours_leg = dist_km / speed_kmh
            current_time += timedelta(hours=hours_leg)
            
            profile.append({
                "node_idx": i,
                "lat": curr["lat"],
                "lon": curr["lon"],
                "eta": current_time,
                "distance_from_prev_km": round(dist_km, 2)
            })
            
        return profile

    def _fetch_unique_environments(self, profile: List[Dict]) -> Dict[str, Any]:
        """
        Prevents N+1 API problem by batching/caching unique grid coordinates.
        (Implementation assumes marine_service has a batched or cached retrieval).
        """
        # For spatial deduplication: round coordinates to nearest 0.1 deg (approx 11km)
        unique_grids = {}
        for node in profile:
            grid_key = f"{round(node['lat'], 1)}_{round(node['lon'], 1)}"
            if grid_key not in unique_grids:
                # Fetch environment for the node's specific ETA
                unique_grids[grid_key] = self.marine_service.get_environment(node["lat"], node["lon"], node["eta"])
        return unique_grids

    def generate_route_profile(self, route_coords: List[Dict[str, float]], vessel: VesselProfile, departure_time: datetime) -> Dict[str, Any]:
        """
        v2.3-B & v2.3-C: Temporal BSI Evaluation & Aggregation.
        """
        profile_nodes = self.compute_etas(route_coords, vessel, departure_time)
        if not profile_nodes:
            return {}
            
        unique_grids = self._fetch_unique_environments(profile_nodes)
        
        evaluated_profile = []
        max_bsi = 0
        sum_severity = 0.0
        peak_node = 0
        peak_eta = departure_time
        high_severity_count = 0
        
        for node in profile_nodes:
            grid_key = f"{round(node['lat'], 1)}_{round(node['lon'], 1)}"
            env_timeline = unique_grids[grid_key]
            
            # v2.3-B: Temporal Slicing (extract conditions exactly at node['eta'])
            # We mock time-slicing logic by passing the ETA to the snapshot generator
            # (In production, the marine service extracts the exact hour index from the 72h cache)
            snapshot_at_eta = env_timeline.get_slice_at(node["eta"]) if hasattr(env_timeline, 'get_slice_at') else env_timeline
            
            bsi_result = self.bsi_engine.evaluate(snapshot_at_eta, vessel)
            
            node_severity = bsi_result["severity_score"]
            node_bsi = bsi_result["bsi"]
            
            # Aggregation logic
            sum_severity += node_severity
            if node_severity > max_bsi:
                max_bsi = node_severity
                peak_node = node["node_idx"]
                peak_eta = node["eta"]
                
            if node_severity >= 60: # 60+ is considered high severity
                high_severity_count += 1
                
            evaluated_profile.append({
                "node": node["node_idx"],
                "lat": node["lat"],
                "lon": node["lon"],
                "eta": node["eta"].isoformat(),
                "bsi": node_bsi,
                "severity": node_severity
            })
            
        mean_severity = sum_severity / len(evaluated_profile)
        
        # Calculate duration in high severity (approx based on node spacing)
        # For simplicity in v2.3, treat each node as a fraction of total time
        total_trip_hours = (profile_nodes[-1]["eta"] - profile_nodes[0]["eta"]).total_seconds() / 3600.0
        high_risk_duration = (high_severity_count / len(evaluated_profile)) * total_trip_hours
        
        # Convert ETAs to isoformat for API output
        peak_eta_iso = peak_eta.isoformat() if isinstance(peak_eta, datetime) else peak_eta
        for p in evaluated_profile:
            if isinstance(p["eta"], datetime):
                p["eta"] = p["eta"].isoformat()
                
        return {
            "route_bsi": {
                "current": evaluated_profile[0]["bsi"],
                "maximum": max_bsi,
                "mean_severity": round(mean_severity, 1),
                "peak_node": peak_node,
                "peak_eta": peak_eta_iso,
                "high_severity_duration_hours": round(high_risk_duration, 1)
            },
            "profile": evaluated_profile
        }

    def optimize_departure(self, route_coords: List[Dict[str, float]], vessel: VesselProfile, base_departure: datetime) -> Dict[str, Any]:
        """
        v2.3-D: Departure Optimization.
        Compares multiple departure windows to find the safest recommendation.
        """
        windows = [0, 1, 2, 3] # Compare T+0, T+1, T+2, T+3 hours
        options = []
        
        best_departure = base_departure
        lowest_peak = 999
        
        for hour_offset in windows:
            test_departure = base_departure + timedelta(hours=hour_offset)
            profile_data = self.generate_route_profile(route_coords, vessel, test_departure)
            
            peak_sev = profile_data["route_bsi"]["maximum"]
            options.append({
                "departure_time": test_departure.isoformat(),
                "peak_severity": peak_sev,
                "mean_severity": profile_data["route_bsi"]["mean_severity"]
            })
            
            # Tie-break rule: earliest departure when multiple departures have equal minimum peak severity.
            # Using strictly less than `<` ensures that a later departure tying the lowest peak 
            # does NOT overwrite the earlier departure.
            if peak_sev < lowest_peak:
                lowest_peak = peak_sev
                best_departure = test_departure
                
        return {
            "recommended_departure": best_departure.isoformat(),
            "alternatives": options,
            "rationale": f"Expected peak severity decreases to {lowest_peak} by departing at {best_departure.strftime('%H:%M')}."
        }
