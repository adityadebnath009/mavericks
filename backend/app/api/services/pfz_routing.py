import math
import heapq
from datetime import datetime, timedelta
import logging

from app.api.services.forecast_data import ForecastDataService
from app.api.endpoints.geofence import evaluate_geofence_offline
from app.core.exceptions import DataUnavailableError

logger = logging.getLogger(__name__)

# ==============================================================================
# SIH26176 - NAVIK MARINE RISK & PHYSICS THRESHOLDS
# ==============================================================================
# 1. Capsize Safety Limit: wave_height_m >= critical_height (1.5 * beam_m)
# 2. Risk Tiers (Deterministic Floors):
#    - MODERATE (>= 1.0m or BSI >= 1)
#    - HIGH (>= 2.0m or BSI >= 2)
#    - EXTREME (BSI >= 4 or wave >= critical_height)
# 3. Vessel Length Penalty:
#    - Used to prune extreme hazards (wave > length_m * 0.5)
# ==============================================================================

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
    def calculate_optimal_route(cls, start_lat, start_lon, end_lat, end_lon, beam_m, cruising_speed_kn, departure_time, length_m=10.0):
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
        vessel_speed_kmh = cruising_speed_kn * 1.852
        critical_height = beam_m * 1.5

        all_nodes = set(ForecastDataService.get_grid_nodes())
        all_nodes.add(start_node)
        all_nodes.add(end_node)

        try:
            start_gf = evaluate_geofence_offline(start_lat, start_lon)
            if start_gf.get("is_inside_mpa") or not start_gf.get("is_inside_eez"):
                return {"route_coords": [], "snapshots": [], "decision": "REJECTED_NO_SAFE_ROUTE"}
                
            end_gf = evaluate_geofence_offline(end_lat, end_lon)
            if end_gf.get("is_inside_mpa") or not end_gf.get("is_inside_eez"):
                return {"route_coords": [], "snapshots": [], "decision": "REJECTED_NO_SAFE_ROUTE"}
        except Exception as e:
            raise DataUnavailableError(f"Geofence data unavailable: {str(e)}")

        queue = []
        heapq.heappush(queue, (0.0, start_node, dep_dt, [(start_node, dep_dt)]))
        visited = set()
        shortest_path = None
        
        geofence_cache = {start_node: start_gf, end_node: end_gf}
        env_cache = {}

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
                    except Exception as e:
                        raise DataUnavailableError(f"Geofence data unavailable: {str(e)}")
                        
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
                    
                if env.wave_height_m >= critical_height or env.bsi >= 4 or env.wave_height_m > (length_m * 0.5):
                    continue
                    
                boat_bearing = cls.calculate_bearing(u_lat, u_lon, v[0], v[1])
                delta_theta = math.radians(env.current_direction_deg - boat_bearing)
                curr_speed_kmh = env.current_speed_ms * 3.6
                curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                delta_v = 0.1 * (env.wave_height_m ** 2) + 0.04 * env.wind_speed_kmh
                effective_boat_speed = vessel_speed_kmh - delta_v
                max_hull_speed = max(30.0, 2.5 * math.sqrt(length_m)) 
                effective_boat_speed = min(effective_boat_speed, max_hull_speed)
                
                effective_speed = min(30.0, effective_boat_speed + curr_parallel_kmh)
                
                if effective_speed <= 0:
                    continue
                    
                transit_time_hrs = dist / effective_speed
                exact_arrival_time = u_time + timedelta(hours=transit_time_hrs)

                bsi_penalty = 5.0 * (env.bsi ** 2)
                border_penalty = 20.0 if gf.get("distance_to_border_km", 999.0) < 5.0 else 0.0

                edge_cost = transit_time_hrs + bsi_penalty + border_penalty
                heapq.heappush(queue, (cost + edge_cost, v, exact_arrival_time, path + [(v, exact_arrival_time)]))

        if not shortest_path:
            return {"route_coords": [], "snapshots": [], "decision": "REJECTED_NO_SAFE_ROUTE"}

        snapshots = []
        segments = []
        current_segment_coords = []
        current_segment_risk = None
        current_segment_reason = None
        segment_index = 0
        
        for idx, (node, exact_time) in enumerate(shortest_path):
            try:
                env = ForecastDataService.get_environment(node[0], node[1], exact_time)
                
                risk_lvl = "LOW"
                reason = "Optimal sea state"
                
                if env.wave_height_m >= critical_height or env.bsi >= 4 or env.wave_height_m > (length_m * 0.5):
                    risk_lvl = "EXTREME"
                    reason = "Capsize or length limit exceeded"
                elif env.wave_height_m >= 2.0 or env.bsi >= 2:
                    risk_lvl = "HIGH"
                    reason = "Dangerous wave heights or steepness"
                elif env.wave_height_m >= 1.0 or env.bsi >= 1:
                    risk_lvl = "MODERATE"
                    reason = "Elevated sea state"
                    
                snapshots.append({
                    "time": exact_time.isoformat(),
                    "lat": node[0],
                    "lon": node[1],
                    "wave_height_m": round(env.wave_height_m, 2),
                    "wind_speed_kmh": round(env.wind_speed_kmh, 2),
                    "wind_direction_deg": round(env.wind_direction_deg, 2),
                    "current_speed_ms": round(env.current_speed_ms, 2),
                    "current_direction_deg": round(env.current_direction_deg, 2),
                    "bsi": env.bsi,
                    "risk": risk_lvl
                })
                
                if current_segment_risk is None:
                    current_segment_risk = risk_lvl
                    current_segment_reason = reason
                    current_segment_coords.append([node[1], node[0]])
                elif current_segment_risk != risk_lvl:
                    segments.append({
                        "segment_index": segment_index,
                        "coordinates": current_segment_coords,
                        "risk": current_segment_risk,
                        "reason": current_segment_reason
                    })
                    segment_index += 1
                    current_segment_coords = [current_segment_coords[-1], [node[1], node[0]]]
                    current_segment_risk = risk_lvl
                    current_segment_reason = reason
                else:
                    current_segment_coords.append([node[1], node[0]])
                
            except DataUnavailableError:
                pass

        if current_segment_coords and len(current_segment_coords) > 1:
            segments.append({
                "segment_index": segment_index,
                "coordinates": current_segment_coords,
                "risk": current_segment_risk,
                "reason": current_segment_reason
            })

        return {
            "decision": "RECOMMENDED",
            "route_coords": [[n[0][1], n[0][0]] for n in shortest_path],
            "snapshots": snapshots,
            "segments": segments
        }
