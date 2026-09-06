import math
import heapq
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional

from app.api.services.forecast_data import ForecastDataService
from app.api.endpoints.geofence import evaluate_geofence_offline
from app.core.exceptions import DataUnavailableError
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.api.services.route_bsi_profiler import RouteBsiProfiler

logger = logging.getLogger(__name__)

# Palk Strait High-Resolution Corridor (0.1 degree spacing)
# Allows the A* engine to mathematically traverse the narrow gap between India and Sri Lanka
# without stepping outside the 'india_eez' Geofence boundary polygon.
PALK_STRAIT_CORRIDOR_NODES = [
    (9.0, 79.1), (9.0, 79.2), (9.0, 79.3), (9.0, 79.4), (9.0, 79.5), (9.1, 79.1), (9.1, 79.2), 
    (9.1, 79.3), (9.1, 79.4), (9.1, 79.5), (9.2, 79.2), (9.2, 79.3), (9.2, 79.4), (9.2, 79.5), 
    (9.3, 79.1), (9.3, 79.2), (9.3, 79.4), (9.3, 79.5), (9.4, 79.1), (9.4, 79.2), (9.4, 79.3), 
    (9.4, 79.4), (9.5, 79.1), (9.5, 79.2), (9.5, 79.3), (9.5, 79.4), (9.6, 79.1), (9.6, 79.2), 
    (9.6, 79.3), (9.6, 79.4), (9.7, 79.1), (9.7, 79.2), (9.7, 79.3), (9.8, 79.1), (9.8, 79.2), 
    (9.8, 79.3), (9.8, 79.4), (9.9, 79.2), (9.9, 79.3), (9.9, 79.4), (9.9, 79.5), (10.0, 79.3), 
    (10.0, 79.4), (10.0, 79.5), (10.0, 79.6), (10.0, 79.7), (10.1, 79.3), (10.1, 79.4), (10.1, 79.5), 
    (10.1, 79.6), (10.1, 79.7), (10.2, 79.3), (10.2, 79.4), (10.2, 79.5), (10.2, 79.6), (10.2, 79.7), 
    (10.3, 79.4), (10.3, 79.5), (10.3, 79.7)
]

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

class PFZRoutingService:
    @staticmethod
    def calculate_bearing(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
        initial_bearing = math.atan2(x, y)
        return (math.degrees(initial_bearing) + 360) % 360

    @classmethod
    def calculate_optimal_route(cls, start_lat: float, start_lon: float, end_lat: float, end_lon: float, vessel_profile=None, departure_time: str = None, optimize_departure: bool = False, beam_m: float = None, cruising_speed_kn: float = None, **kwargs):
        # Backward compatibility for old positional/keyword arguments
        if not isinstance(vessel_profile, VesselProfile):
            # If vessel_profile is a float/int, it's actually beam_m from the old signature: 
            # (start_lat, start_lon, end_lat, end_lon, beam_m, cruising_speed_kn, departure_time)
            if isinstance(vessel_profile, (float, int)):
                beam_m_val = vessel_profile
                cruising_speed_kn_val = departure_time
                departure_time_val = optimize_departure
                optimize_departure_val = kwargs.get('optimize_departure', False) if 'optimize_departure' in kwargs else False
                vessel_profile = VesselProfile(length_m=beam_m_val * 5.0, beam_m=beam_m_val, cruising_speed_kn=cruising_speed_kn_val)
                departure_time = departure_time_val
                optimize_departure = optimize_departure_val
            else:
                # kwargs backwards compatibility
                if beam_m is not None and cruising_speed_kn is not None:
                    vessel_profile = VesselProfile(length_m=beam_m * 5.0, beam_m=beam_m, cruising_speed_kn=cruising_speed_kn)
                else:
                    raise ValueError("vessel_profile must be provided as a VesselProfile instance")

        try:
            dep_dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
        except Exception as e:
            raise DataUnavailableError(f"Invalid departure time: {str(e)}")
            
        try:
            ForecastDataService.get_environment(start_lat, start_lon, dep_dt)
        except DataUnavailableError as e:
            raise DataUnavailableError(f"Start location unavailable: {str(e)}")
            
        start_node = (start_lat, start_lon)
        end_node = (end_lat, end_lon)
        vessel_speed_kmh = vessel_profile.cruising_speed_kn * 1.852
        
        all_nodes = set(ForecastDataService.get_grid_nodes())
        all_nodes.update(PALK_STRAIT_CORRIDOR_NODES)
        all_nodes.add(start_node)
        all_nodes.add(end_node)

        try:
            start_gf = evaluate_geofence_offline(start_lat, start_lon)
            if start_gf.get("is_inside_mpa") or not start_gf.get("is_inside_eez"):
                return {"decision": "REJECTED_NO_SAFE_ROUTE"}
                
            end_gf = evaluate_geofence_offline(end_lat, end_lon)
            if end_gf.get("is_inside_mpa") or not end_gf.get("is_inside_eez"):
                return {"decision": "REJECTED_NO_SAFE_ROUTE"}
        except Exception as e:
            raise DataUnavailableError(f"Geofence data unavailable: {str(e)}")

        queue = []
        heapq.heappush(queue, (0.0, start_node, dep_dt, [(start_node, dep_dt)]))
        visited = set()
        shortest_path = None
        
        geofence_cache = {start_node: start_gf, end_node: end_gf}
        env_cache = {}
        
        orca_engine = OrcaBsiEngine()

        while queue:
            cost, u, u_time, path = heapq.heappop(queue)

            state_key = (u, u_time.strftime('%Y%m%d%H'))
            if state_key in visited:
                continue
            visited.add(state_key)

            if (u_time - dep_dt).total_seconds() > 72 * 3600:
                continue

            if u == end_node or haversine_distance(u[0], u[1], end_node[0], end_node[1]) < 5.0:
                if u != end_node:
                    path.append((end_node, u_time))
                shortest_path = path
                break

            u_lat, u_lon = u
            for v in all_nodes:
                if u == v or abs(v[0] - u_lat) > 0.65 or abs(v[1] - u_lon) > 0.65:
                    continue
                dist = haversine_distance(u_lat, u_lon, v[0], v[1])
                
                if v not in geofence_cache:
                    try:
                        gf = evaluate_geofence_offline(v[0], v[1])
                        geofence_cache[v] = gf
                    except Exception:
                        continue
                        
                gf = geofence_cache[v]
                if gf.get("is_inside_mpa") or not gf.get("is_inside_eez"):
                    continue
                    
                rough_transit = dist / vessel_speed_kmh
                arrival_time = u_time + timedelta(hours=rough_transit)
                
                env_cache_key = (v[0], v[1], arrival_time.strftime('%Y%m%d%H'))
                if env_cache_key not in env_cache:
                    try:
                        env_cache[env_cache_key] = ForecastDataService.get_environment(v[0], v[1], arrival_time)
                    except DataUnavailableError:
                        env_cache[env_cache_key] = None
                        
                env = env_cache[env_cache_key]
                if env is None:
                    continue
                    
                bsi_result = orca_engine.evaluate(env, vessel_profile)
                severity = bsi_result["severity_score"]
                
                critical_height = vessel_profile.beam_m * 1.5 if vessel_profile.beam_m else 4.0
                if env.wave_height_m >= critical_height or severity >= 100 or env.wave_height_m > (vessel_profile.length_m * 0.5):
                    continue
                    
                boat_bearing = cls.calculate_bearing(u_lat, u_lon, v[0], v[1])
                delta_theta = math.radians(env.current_direction_deg - boat_bearing)
                curr_speed_kmh = env.current_speed_ms * 3.6
                curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                delta_v = 0.1 * (env.wave_height_m ** 2) + 0.04 * env.wind_speed_kmh
                effective_boat_speed = vessel_speed_kmh - delta_v
                max_hull_speed = max(30.0, 2.5 * math.sqrt(vessel_profile.length_m)) 
                effective_boat_speed = min(effective_boat_speed, max_hull_speed)
                
                effective_speed = min(30.0, effective_boat_speed + curr_parallel_kmh)
                
                if effective_speed <= 0:
                    continue
                    
                transit_time_hrs = dist / effective_speed
                exact_arrival_time = u_time + timedelta(hours=transit_time_hrs)

                # Normalized Penalty Math: P_BSI = lambda * s^gamma
                lam = 10.0
                gamma = 2.0
                s = severity / 100.0
                bsi_penalty = lam * (s ** gamma)
                border_penalty = 20.0 if gf.get("distance_to_border_km", 999.0) < 5.0 else 0.0

                edge_cost = transit_time_hrs + bsi_penalty + border_penalty
                heapq.heappush(queue, (cost + edge_cost, v, exact_arrival_time, path + [(v, exact_arrival_time)]))

        if not shortest_path:
            return None

        # Build response schema
        route_coords = [{"lat": n[0], "lon": n[1]} for n, t in shortest_path]
        
        profiler = RouteBsiProfiler(ForecastDataService, orca_engine)
        base_profile = profiler.generate_route_profile(route_coords, vessel_profile, dep_dt)
        
        best_departure = dep_dt
        selected_peak_severity = base_profile["route_bsi"]["maximum"]
        shortest_route_peak_severity = base_profile["route_bsi"]["maximum"] 
        additional_distance_km = 0.0
        additional_duration_minutes = 0
        
        if optimize_departure:
            opt_result = profiler.optimize_departure(route_coords, vessel_profile, dep_dt)
            best_departure_str = opt_result["recommended_departure"]
            best_departure = datetime.fromisoformat(best_departure_str)
            selected_peak_severity = min(opt_result["alternatives"], key=lambda x: x["peak_severity"])["peak_severity"]
            if best_departure != dep_dt:
                base_profile = profiler.generate_route_profile(route_coords, vessel_profile, best_departure)

        path_output = []
        snapshots = []
        critical_height = vessel_profile.beam_m * 1.5 if vessel_profile.beam_m else 4.0
        
        for p in base_profile["profile"]:
            path_output.append({
                "node_id": p["node"],
                "lat": p["lat"],
                "lon": p["lon"],
                "eta": p["eta"],
                "severity_score": p["severity"]
            })
            try:
                eta_dt = datetime.fromisoformat(p["eta"]) if isinstance(p["eta"], str) else p["eta"]
                env = ForecastDataService.get_environment(p["lat"], p["lon"], eta_dt)
                
                risk_lvl = "LOW"
                if env.wave_height_m >= critical_height or p["severity"] >= 100 or env.wave_height_m > (vessel_profile.length_m * 0.5):
                    risk_lvl = "EXTREME"
                elif env.wave_height_m >= 2.0 or p["severity"] >= 50:
                    risk_lvl = "HIGH"
                elif env.wave_height_m >= 1.0 or p["severity"] >= 25:
                    risk_lvl = "MODERATE"
                    
                snapshots.append({
                    "time": p["eta"],
                    "lat": p["lat"],
                    "lon": p["lon"],
                    "wave_height_m": round(env.wave_height_m, 2),
                    "wind_speed_kmh": round(env.wind_speed_kmh, 2),
                    "wind_direction_deg": round(env.wind_direction_deg, 2),
                    "current_speed_ms": round(env.current_speed_ms, 2),
                    "current_direction_deg": round(env.current_direction_deg, 2),
                    "bsi": p["severity"],
                    "risk": risk_lvl
                })
            except Exception:
                pass
        total_dist = sum(haversine_distance(route_coords[i-1]["lat"], route_coords[i-1]["lon"], route_coords[i]["lat"], route_coords[i]["lon"]) for i in range(1, len(route_coords)))
        total_dur_hours = (datetime.fromisoformat(path_output[-1]["eta"]) - datetime.fromisoformat(path_output[0]["eta"])).total_seconds() / 3600.0

        return {
            "decision": "RECOMMENDED",
            "route": {
                "distance_km": round(total_dist, 1),
                "duration_hours": round(total_dur_hours, 1)
            },
            "optimization": {
                "objective": "minimize_predicted_max_severity",
                "shortest_route_peak_severity": int(shortest_route_peak_severity),
                "selected_route_peak_severity": int(selected_peak_severity),
                "additional_distance_km": additional_distance_km,
                "additional_duration_minutes": additional_duration_minutes
            },
            "path": path_output,
            "route_coords": route_coords,
            "snapshots": [{"time": p["eta"], "bsi": p["severity_score"], **p} for p in path_output]
        }
