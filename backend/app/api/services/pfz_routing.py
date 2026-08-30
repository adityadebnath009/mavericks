import math
import heapq
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from sqlalchemy.orm import Session
from app.api.endpoints.geofence import evaluate_geofence_offline
from app.api.services.pfz_intelligence import haversine_distance
from app.api.services.forecast_data import ForecastDataService
from app.core.exceptions import DataUnavailableError

logger = logging.getLogger(__name__)

class PFZRoutingService:
    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
        bearing_rad = math.atan2(y, x)
        return (math.degrees(bearing_rad) + 360.0) % 360.0

    @classmethod
    def calculate_optimal_route(
        cls,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        beam_m: float,
        cruising_speed_kn: float,
        departure_time: str,
    ) -> dict:
        vessel_speed_kmh = cruising_speed_kn * 1.852
        critical_height = 1.5 * beam_m
        
        # 1. Resolve starting time
        try:
            dt_str = departure_time.replace("Z", "")
            if "T" in dt_str:
                dep_dt = datetime.fromisoformat(dt_str)
            else:
                dep_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception as parse_err:
            raise DataUnavailableError(f"Invalid departure_time '{departure_time}'") from parse_err

        # Validate start and end nodes are in the forecast domain immediately
        try:
            ForecastDataService.get_environment(start_lat, start_lon, dep_dt)
        except DataUnavailableError as e:
            raise DataUnavailableError(f"Start location unavailable: {str(e)}")

        # 2. Get active grid nodes
        grid_nodes = ForecastDataService.get_grid_nodes()
        # Ensure start and end are in the search space
        start_node = (start_lat, start_lon)
        end_node = (end_lat, end_lon)
        all_nodes = set(grid_nodes)
        all_nodes.add(start_node)
        all_nodes.add(end_node)

        # 3. Dijkstra Setup
        queue = []
        heapq.heappush(queue, (0.0, start_node, dep_dt, [start_node]))
        visited = set()
        shortest_path = None
        
        geofence_cache = {}

        while queue:
            cost, u, u_time, path = heapq.heappop(queue)

            if u in visited:
                continue
            visited.add(u)

            if u == end_node or haversine_distance(u[0], u[1], end_node[0], end_node[1]) < 5.0:
                if u != end_node:
                    path.append(end_node)
                shortest_path = path
                break

            u_lat, u_lon = u
            for v in all_nodes:
                # Find valid neighbors on the grid (approx < 75km apart to bound search)
                if abs(v[0] - u_lat) <= 0.65 and abs(v[1] - u_lon) <= 0.65 and v != u:
                    dist = haversine_distance(u_lat, u_lon, v[0], v[1])
                    
                    # 4. Geofencing Strict Check
                    if v not in geofence_cache:
                        try:
                            gf = evaluate_geofence_offline(v[0], v[1])
                            geofence_cache[v] = gf
                        except Exception as e:
                            # Fails closed on geofence error
                            geofence_cache[v] = None
                            
                    gf = geofence_cache[v]
                    if gf is None or gf.get("is_inside_mpa") or not gf.get("is_inside_eez"):
                        continue
                        
                    # 5. Environment at estimated arrival
                    # Base transit time roughly estimating speed for u_time propagation
                    rough_transit = dist / vessel_speed_kmh
                    arrival_time = u_time + timedelta(hours=rough_transit)
                    
                    try:
                        env = ForecastDataService.get_environment(v[0], v[1], arrival_time)
                    except DataUnavailableError:
                        continue # Impassable due to missing data (land / out of bounds)
                        
                    # Hard capsize constraint
                    if env.wave_height_m >= critical_height or env.bsi >= 4:
                        continue
                        
                    # Speed physics
                    boat_bearing = cls.calculate_bearing(u_lat, u_lon, v[0], v[1])
                    delta_theta = math.radians(env.current_direction_deg - boat_bearing)
                    curr_speed_kmh = env.current_speed_ms * 3.6
                    curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                    delta_v = 0.1 * (env.wave_height_m ** 2) + 0.04 * env.wind_speed_kmh
                    effective_boat_speed = max(2.0, vessel_speed_kmh - delta_v)
                    effective_speed = max(2.0, min(30.0, effective_boat_speed + curr_parallel_kmh))
                    transit_time_hrs = dist / effective_speed
                    
                    exact_arrival_time = u_time + timedelta(hours=transit_time_hrs)

                    bsi_penalty = 5.0 * (env.bsi ** 2)
                    border_penalty = 20.0 if gf.get("distance_to_border_km", 999.0) < 5.0 else 0.0

                    edge_cost = transit_time_hrs + bsi_penalty + border_penalty
                    heapq.heappush(queue, (cost + edge_cost, v, exact_arrival_time, path + [v]))

        # No safe route found
        if not shortest_path:
            return {"route_coords": [], "decision": "REJECTED_NO_SAFE_ROUTE"}

        # 6. Build route snapshots and segments
        snapshots = []
        segments = []
        current_time = dep_dt
        
        current_segment_coords = []
        current_segment_risk = None
        current_segment_reason = None
        segment_index = 0
        
        for idx, node in enumerate(shortest_path):
            # Calculate Risk Level (Deterministic Floors)
            # LOW: < 1.0m hs, BSI 0
            # MODERATE: >= 1.0m hs or BSI >= 1
            # HIGH: >= 2.0m hs or BSI >= 2
            # EXTREME: >= critical_height or BSI >= 4
            
            try:
                env = ForecastDataService.get_environment(node[0], node[1], current_time)
                
                risk_lvl = "LOW"
                reason = "Optimal sea state"
                
                if env.wave_height_m >= critical_height or env.bsi >= 4:
                    risk_lvl = "EXTREME"
                    reason = "Capsize limit exceeded"
                elif env.wave_height_m >= 2.0 or env.bsi >= 2:
                    risk_lvl = "HIGH"
                    reason = "Dangerous wave heights or steepness"
                elif env.wave_height_m >= 1.0 or env.bsi >= 1:
                    risk_lvl = "MODERATE"
                    reason = "Elevated sea state"
                    
                snapshots.append({
                    "time": current_time.isoformat(),
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
                
                # Segment Logic
                if current_segment_risk is None:
                    current_segment_risk = risk_lvl
                    current_segment_reason = reason
                    current_segment_coords.append([node[1], node[0]])
                elif current_segment_risk != risk_lvl:
                    # Risk changed, seal the old segment
                    segments.append({
                        "segment_index": segment_index,
                        "coordinates": current_segment_coords,
                        "risk": current_segment_risk,
                        "reason": current_segment_reason
                    })
                    segment_index += 1
                    # Start new segment, overlapping by the current node
                    current_segment_coords = [current_segment_coords[-1], [node[1], node[0]]]
                    current_segment_risk = risk_lvl
                    current_segment_reason = reason
                else:
                    current_segment_coords.append([node[1], node[0]])
                
            except DataUnavailableError:
                pass
                
            if idx < len(shortest_path) - 1:
                next_node = shortest_path[idx+1]
                dist = haversine_distance(node[0], node[1], next_node[0], next_node[1])
                try:
                    env = ForecastDataService.get_environment(node[0], node[1], current_time)
                    boat_bearing = cls.calculate_bearing(node[0], node[1], next_node[0], next_node[1])
                    delta_theta = math.radians(env.current_direction_deg - boat_bearing)
                    curr_speed_kmh = env.current_speed_ms * 3.6
                    curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                    delta_v = 0.1 * (env.wave_height_m ** 2) + 0.04 * env.wind_speed_kmh
                    effective_boat_speed = max(2.0, vessel_speed_kmh - delta_v)
                    effective_speed = max(2.0, min(30.0, effective_boat_speed + curr_parallel_kmh))
                except DataUnavailableError:
                    effective_speed = min(30.0, vessel_speed_kmh)

                current_time += timedelta(hours=dist / effective_speed)

        if current_segment_coords and len(current_segment_coords) > 1:
            segments.append({
                "segment_index": segment_index,
                "coordinates": current_segment_coords,
                "risk": current_segment_risk,
                "reason": current_segment_reason
            })

        return {
            "decision": "RECOMMENDED",
            "route_coords": [[n[1], n[0]] for n in shortest_path],
            "snapshots": snapshots,
            "segments": segments
        }
