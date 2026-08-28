import os
import json
import math
import heapq
import logging
from sqlalchemy.orm import Session
from app.api.endpoints.geofence import evaluate_geofence_offline
from app.api.services.pfz_intelligence import haversine_distance

logger = logging.getLogger(__name__)

class PFZRoutingService:
    """
    Dijkstra-based weather-aware routing service using WW3, currents,
    wind, BSI, and PostGIS geofencing restrictions in the North Indian Ocean.
    """

    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the bearing (compass heading) from point 1 to point 2.
        Returns bearing in degrees (0 to 360).
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        return (bearing_deg + 360.0) % 360.0

    @classmethod
    def get_interpolated_properties(cls, lat: float, lon: float, t_current: float, loaded_grids: dict) -> dict:
        """
        Calculates environmental variables at a specific latitude, longitude, and elapsed time
        by interpolating between adjacent 3-hour forecast steps.
        """
        t_current = max(0.0, min(71.99, t_current))
        day = int(t_current // 24) + 1
        hour_of_day = t_current % 24
        
        h1 = int(hour_of_day // 3) * 3
        h2 = h1 + 3
        day2 = day
        if h2 >= 24:
            h2 = 0
            day2 = day + 1
            if day2 > 3:
                day2 = 3
                h2 = 21
                
        w = (hour_of_day - h1) / 3.0
        
        grid_lat = round(round(lat * 2.0) / 2.0, 4)
        grid_lon = round(round(lon * 2.0) / 2.0, 4)
        node_key = (grid_lat, grid_lon)
        
        default_props = {
            "bsi": 0, "hs": 1.0, "wind_speed_kmh": 15.0, "current_speed_ms": 0.25,
            "wind_dir_deg": 180.0, "current_dir_deg": 112.0,
            "stp": 0.015, "spr": 0.25, "hsea_initial": 0.7, "hsea_final": 0.7
        }
        
        map1 = loaded_grids.get((day, h1), {})
        map2 = loaded_grids.get((day2, h2), {})
        
        prop1 = map1.get(node_key)
        if not prop1 and map1:
            closest_key = min(map1.keys(), key=lambda k: (k[0]-grid_lat)**2 + (k[1]-grid_lon)**2)
            prop1 = map1[closest_key]
        if not prop1:
            prop1 = default_props
            
        prop2 = map2.get(node_key)
        if not prop2 and map2:
            closest_key = min(map2.keys(), key=lambda k: (k[0]-grid_lat)**2 + (k[1]-grid_lon)**2)
            prop2 = map2[closest_key]
        if not prop2:
            prop2 = default_props
            
        # Interpolate scalars
        hs = prop1.get("hs", 1.0) * (1.0 - w) + prop2.get("hs", 1.0) * w
        wind = prop1.get("wind_speed_kmh", 15.0) * (1.0 - w) + prop2.get("wind_speed_kmh", 15.0) * w
        
        # Interpolate current vectors U and V to resolve speed/direction
        c_spd1 = prop1.get("current_speed_ms", 0.25)
        c_dir1 = math.radians(prop1.get("current_dir_deg", 112.0))
        u1 = c_spd1 * math.sin(c_dir1)
        v1 = c_spd1 * math.cos(c_dir1)
        
        c_spd2 = prop2.get("current_speed_ms", 0.25)
        c_dir2 = math.radians(prop2.get("current_dir_deg", 112.0))
        u2 = c_spd2 * math.sin(c_dir2)
        v2 = c_spd2 * math.cos(c_dir2)
        
        u_interp = u1 * (1.0 - w) + u2 * w
        v_interp = v1 * (1.0 - w) + v2 * w
        
        current_speed_ms = math.sqrt(u_interp**2 + v_interp**2)
        current_dir_deg = math.degrees(math.atan2(u_interp, v_interp)) % 360
        
        # Interpolate wind direction using unit vector projections
        def interpolate_angle(a1, a2, weight):
            r1 = math.radians(a1)
            r2 = math.radians(a2)
            sin_interp = math.sin(r1) * (1.0 - weight) + math.sin(r2) * weight
            cos_interp = math.cos(r1) * (1.0 - weight) + math.cos(r2) * weight
            return math.degrees(math.atan2(sin_interp, cos_interp)) % 360
            
        wind_dir_deg = interpolate_angle(prop1.get("wind_dir_deg", 180.0), prop2.get("wind_dir_deg", 180.0), w)
        
        # Dynamic BSI recalculation from physical forecast components
        stp = prop1.get("stp", 0.015) * (1.0 - w) + prop2.get("stp", 0.015) * w
        spr = prop1.get("spr", 0.25) * (1.0 - w) + prop2.get("spr", 0.25) * w
        hsea_init = prop1.get("hsea_initial", 0.7) * (1.0 - w) + prop2.get("hsea_initial", 0.7) * w
        hsea_fin = prop1.get("hsea_final", 0.7) * (1.0 - w) + prop2.get("hsea_final", 0.7) * w
        
        from app.api.services.bsi_calculator import BSICalculator
        bsi = BSICalculator.calculate_bsi(stp, hs, spr, hsea_init, hsea_fin)
        
        return {
            "bsi": bsi,
            "hs": hs,
            "wind_speed_kmh": wind,
            "current_speed_ms": current_speed_ms,
            "current_dir_deg": current_dir_deg,
            "wind_dir_deg": wind_dir_deg,
            "stp": stp,
            "spr": spr,
            "hsea_initial": hsea_init,
            "hsea_final": hsea_fin
        }

    @classmethod
    def calculate_optimal_route(
        cls,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        beam_m: float,
        day: int,
        hour: int,
        db: Session,
        departure_time: str = None
    ) -> dict:
        """
        Executes spatio-temporal Dijkstra routing to resolve the optimal route (Route A)
        and shortest route (Route B), evaluating wind, wave, and current parameters at arrival time.
        """
        import datetime

        # 1. Map departure datetime to hours relative to baseline date (2026-08-26 00:00:00)
        t_start = (day - 1) * 24.0 + hour
        if departure_time:
            try:
                baseline_dt = datetime.datetime(2026, 8, 26, 0, 0, 0)
                dt_str = departure_time.replace("Z", "")
                if "T" in dt_str:
                    dep_dt = datetime.datetime.fromisoformat(dt_str)
                else:
                    dep_dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                elapsed = (dep_dt - baseline_dt).total_seconds() / 3600.0
                t_start = max(0.0, elapsed)
                if t_start > 72.0:
                    t_start = t_start % 72.0
            except Exception as parse_err:
                logger.warning(f"Error parsing departure_time '{departure_time}': {parse_err}. Using default day/hour offset.")

        # 2. Pre-load all 24 safety grids (3 days x 8 steps) into memory
        loaded_grids = {}
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
        for d in [1, 2, 3]:
            for h in [0, 3, 6, 9, 12, 15, 18, 21]:
                cache_path = os.path.join(cache_dir, f"safety_grid_day_{d}_hour_{h}.json")
                if os.path.exists(cache_path):
                    try:
                        with open(cache_path, "r", encoding="utf-8") as f:
                            grid_geojson = json.load(f)
                        features = grid_geojson.get("features", [])
                        nodes_map = {}
                        for feat in features:
                            props = feat["properties"]
                            c_lat = props.get("center_lat")
                            c_lon = props.get("center_lon")
                            if c_lat is not None and c_lon is not None:
                                node_key = (round(c_lat, 4), round(c_lon, 4))
                                nodes_map[node_key] = props
                        loaded_grids[(d, h)] = nodes_map
                    except Exception as load_err:
                        logger.error(f"Error pre-loading safety grid {cache_path}: {load_err}")

        # If no cache grid was pre-loaded, find the nearest cached day/hour fallback
        if not loaded_grids:
            raise ValueError("No active grid cells cached in memory.")

        # Resolve starting grid centers
        any_grid = list(loaded_grids.values())[0]
        start_node = min(any_grid.keys(), key=lambda n: haversine_distance(start_lat, start_lon, n[0], n[1]))
        end_node = min(any_grid.keys(), key=lambda n: haversine_distance(end_lat, end_lon, n[0], n[1]))

        geofence_cache = {}

        # 3. Route A: Spatio-Temporal Dijkstra search (Safest & Current-Optimized Path)
        # Queue: (cost, node, arrival_time_hours, path)
        queue = [(0.0, start_node, t_start, [start_node])]
        visited = {}
        shortest_path = None
        final_time_a = t_start

        while queue:
            (cost, u, u_time, path) = heapq.heappop(queue)

            if u in visited and visited[u] <= cost:
                continue
            visited[u] = cost

            if u == end_node:
                shortest_path = path
                final_time_a = u_time
                break

            u_lat, u_lon = u
            for v in any_grid.keys():
                if abs(v[0] - u_lat) <= 0.65 and abs(v[1] - u_lon) <= 0.65 and v != u:
                    dist = haversine_distance(u_lat, u_lon, v[0], v[1])
                    
                    # Interpolate parameters at arrival time
                    props_v = cls.get_interpolated_properties(v[0], v[1], u_time, loaded_grids)
                    hs = props_v["hs"]
                    wind = props_v["wind_speed_kmh"]
                    bsi = props_v["bsi"]
                    curr_speed_ms = props_v["current_speed_ms"]
                    curr_dir_deg = props_v["current_dir_deg"]

                    # Current vector projection
                    boat_bearing = cls.calculate_bearing(u_lat, u_lon, v[0], v[1])
                    delta_theta = math.radians(curr_dir_deg - boat_bearing)
                    curr_speed_kmh = curr_speed_ms * 3.6
                    curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                    # Dynamic speed loss calculation
                    vessel_speed = 15.0  # km/h
                    delta_v = 0.1 * (hs ** 2) + 0.04 * wind
                    effective_boat_speed = max(2.0, vessel_speed - delta_v)
                    effective_speed = effective_boat_speed + curr_parallel_kmh
                    effective_speed = max(2.0, min(30.0, effective_speed))
                    transit_time = dist / effective_speed

                    # BSI safety penalty weight
                    bsi_penalty = 5.0 * (bsi ** 2)

                    # Hard constraint: Wave height vs Beam capsize floor
                    critical_height = 1.5 * beam_m
                    if hs >= critical_height:
                        continue

                    # Geofencing containment queries
                    if v not in geofence_cache:
                        try:
                            geofence_cache[v] = evaluate_geofence_offline(v[0], v[1])
                        except Exception:
                            geofence_cache[v] = {
                                "is_inside_eez": True,
                                "is_inside_mpa": False,
                                "distance_to_border_km": 999.0
                            }

                    gf = geofence_cache[v]
                    if gf.get("is_inside_mpa") or not gf.get("is_inside_eez"):
                        continue

                    border_penalty = 0.0
                    if gf.get("distance_to_border_km", 999.0) < 5.0:
                        border_penalty = 20.0

                    edge_cost = transit_time + bsi_penalty + border_penalty
                    heapq.heappush(queue, (cost + edge_cost, v, u_time + transit_time, path + [v]))

        if not shortest_path:
            shortest_path = [start_node, end_node]

        # 4. Route B: Shortest Path Dijkstra Search (Optimizing distance while avoiding restricted zones)
        queue_b = [(0.0, start_node, t_start, [start_node])]
        visited_b = {}
        shortest_path_b = None
        final_time_b = t_start

        while queue_b:
            (cost_b, u_b, u_b_time, path_b) = heapq.heappop(queue_b)

            if u_b in visited_b and visited_b[u_b] <= cost_b:
                continue
            visited_b[u_b] = cost_b

            if u_b == end_node:
                shortest_path_b = path_b
                final_time_b = u_b_time
                break

            u_b_lat, u_b_lon = u_b
            for v in any_grid.keys():
                if abs(v[0] - u_b_lat) <= 0.65 and abs(v[1] - u_b_lon) <= 0.65 and v != u_b:
                    dist = haversine_distance(u_b_lat, u_b_lon, v[0], v[1])

                    if v not in geofence_cache:
                        try:
                            geofence_cache[v] = evaluate_geofence_offline(v[0], v[1])
                        except Exception:
                            geofence_cache[v] = {
                                "is_inside_eez": True,
                                "is_inside_mpa": False,
                                "distance_to_border_km": 999.0
                            }

                    gf = geofence_cache[v]
                    if gf.get("is_inside_mpa") or not gf.get("is_inside_eez"):
                        continue

                    # Calculate transit time at this step to propagate arrival time
                    props_v = cls.get_interpolated_properties(v[0], v[1], u_b_time, loaded_grids)
                    hs = props_v["hs"]
                    wind = props_v["wind_speed_kmh"]
                    curr_speed_ms = props_v["current_speed_ms"]
                    curr_dir_deg = props_v["current_dir_deg"]

                    boat_bearing = cls.calculate_bearing(u_b_lat, u_b_lon, v[0], v[1])
                    delta_theta = math.radians(curr_dir_deg - boat_bearing)
                    curr_speed_kmh = curr_speed_ms * 3.6
                    curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                    delta_v = 0.1 * (hs ** 2) + 0.04 * wind
                    effective_boat_speed = max(2.0, 15.0 - delta_v)
                    effective_speed = max(2.0, min(30.0, effective_boat_speed + curr_parallel_kmh))
                    transit_time = dist / effective_speed

                    edge_cost_b = dist
                    heapq.heappush(queue_b, (cost_b + edge_cost_b, v, u_b_time + transit_time, path_b + [v]))

        if not shortest_path_b:
            shortest_path_b = [start_node, end_node]

        # Helper to format arrival time hours to HH:MM format
        def format_arrival_time(t_hours):
            baseline_dt = datetime.datetime(2026, 8, 26, 0, 0, 0)
            arrival_dt = baseline_dt + datetime.timedelta(hours=t_hours)
            return arrival_dt.strftime("%H:%M")

        # 5. Compile Path Metrics and Diagnostic Snapshots for Route A
        total_distance = 0.0
        total_time = 0.0
        max_bsi = 0
        sum_curr_parallel = 0.0
        num_segments = len(shortest_path) - 1
        route_snapshots_a = []
        curr_time = t_start

        for i in range(len(shortest_path)):
            node = shortest_path[i]
            if i == 0:
                seg_time = t_start
            else:
                prev_node = shortest_path[i-1]
                dist = haversine_distance(prev_node[0], prev_node[1], node[0], node[1])
                total_distance += dist
                
                props_prev = cls.get_interpolated_properties(prev_node[0], prev_node[1], curr_time, loaded_grids)
                hs = props_prev["hs"]
                wind = props_prev["wind_speed_kmh"]
                curr_speed_ms = props_prev["current_speed_ms"]
                curr_dir_deg = props_prev["current_dir_deg"]

                boat_bearing = cls.calculate_bearing(prev_node[0], prev_node[1], node[0], node[1])
                delta_theta = math.radians(curr_dir_deg - boat_bearing)
                curr_speed_kmh = curr_speed_ms * 3.6
                curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                delta_v = 0.1 * (hs ** 2) + 0.04 * wind
                effective_boat_speed = max(2.0, 15.0 - delta_v)
                effective_speed = effective_boat_speed + curr_parallel_kmh
                effective_speed = max(2.0, min(30.0, effective_speed))
                transit_time = dist / effective_speed
                curr_time += transit_time
                seg_time = curr_time
                
            props_v = cls.get_interpolated_properties(node[0], node[1], seg_time, loaded_grids)
            bsi = props_v["bsi"]
            if bsi > max_bsi:
                max_bsi = bsi

            if i > 0:
                prev_node = shortest_path[i-1]
                boat_bearing = cls.calculate_bearing(prev_node[0], prev_node[1], node[0], node[1])
                delta_theta = math.radians(props_v["current_dir_deg"] - boat_bearing)
                curr_parallel_ms = props_v["current_speed_ms"] * math.cos(delta_theta)
                sum_curr_parallel += curr_parallel_ms
                effective_speed_kn = (effective_speed / 1.852)
            else:
                curr_parallel_ms = 0.0
                effective_speed_kn = (15.0 / 1.852)

            route_snapshots_a.append({
                "lat": round(node[0], 4),
                "lon": round(node[1], 4),
                "arrival_time": format_arrival_time(seg_time),
                "wave_height_m": round(props_v["hs"], 2),
                "wind_speed_kmh": round(props_v["wind_speed_kmh"], 1),
                "current_speed_ms": round(props_v["current_speed_ms"], 2),
                "current_parallel_ms": round(curr_parallel_ms, 2),
                "effective_speed_kn": round(effective_speed_kn, 1),
                "bsi": bsi
            })

        total_time = curr_time - t_start

        overall_risk = "LOW"
        if max_bsi >= 4:
            overall_risk = "HIGH"
        elif max_bsi >= 2:
            overall_risk = "MODERATE"

        avg_curr_parallel = sum_curr_parallel / max(1, num_segments)
        current_status = "neutral"
        if avg_curr_parallel > 0.5:
            current_status = "favourable"
        elif avg_curr_parallel < -0.5:
            current_status = "adverse"

        # 6. Compute Path Metrics and Summary for Route B
        total_distance_b = 0.0
        sum_curr_parallel_b = 0.0
        max_bsi_b = 0
        curr_time_b = t_start
        num_segments_b = len(shortest_path_b) - 1

        for i in range(len(shortest_path_b)):
            node = shortest_path_b[i]
            if i > 0:
                prev_node = shortest_path_b[i-1]
                dist = haversine_distance(prev_node[0], prev_node[1], node[0], node[1])
                total_distance_b += dist

                props_prev = cls.get_interpolated_properties(prev_node[0], prev_node[1], curr_time_b, loaded_grids)
                hs = props_prev["hs"]
                wind = props_prev["wind_speed_kmh"]
                curr_speed_ms = props_prev["current_speed_ms"]
                curr_dir_deg = props_prev["current_dir_deg"]

                boat_bearing = cls.calculate_bearing(prev_node[0], prev_node[1], node[0], node[1])
                delta_theta = math.radians(curr_dir_deg - boat_bearing)
                curr_speed_kmh = curr_speed_ms * 3.6
                curr_parallel_kmh = curr_speed_kmh * math.cos(delta_theta)

                delta_v = 0.1 * (hs ** 2) + 0.04 * wind
                effective_boat_speed = max(2.0, 15.0 - delta_v)
                effective_speed = max(2.0, min(30.0, effective_speed))
                transit_time = dist / effective_speed
                curr_time_b += transit_time

            props_v = cls.get_interpolated_properties(node[0], node[1], curr_time_b, loaded_grids)
            bsi = props_v["bsi"]
            if bsi > max_bsi_b:
                max_bsi_b = bsi

            if i > 0:
                prev_node = shortest_path_b[i-1]
                boat_bearing = cls.calculate_bearing(prev_node[0], prev_node[1], node[0], node[1])
                delta_theta = math.radians(props_v["current_dir_deg"] - boat_bearing)
                curr_parallel_ms = props_v["current_speed_ms"] * math.cos(delta_theta)
                sum_curr_parallel_b += curr_parallel_ms

        total_time_b = curr_time_b - t_start

        overall_risk_b = "LOW"
        if max_bsi_b >= 4:
            overall_risk_b = "HIGH"
        elif max_bsi_b >= 2:
            overall_risk_b = "MODERATE"

        avg_curr_parallel_b = sum_curr_parallel_b / max(1, num_segments_b)
        current_status_b = "neutral"
        if avg_curr_parallel_b > 0.5:
            current_status_b = "favourable"
        elif avg_curr_parallel_b < -0.5:
            current_status_b = "adverse"

        # 7. Check avoided hazards along the straight path for summary logs
        avoided_hazards = []
        straight_coords = [[start_lon, start_lat], [end_lon, end_lat]]
        crosses_mpa = False
        crosses_eez_border = False
        crosses_high_risk = False

        for i in range(1, 5):
            t = i / 5.0
            sample_lat = start_lat + t * (end_lat - start_lat)
            sample_lon = start_lon + t * (end_lon - start_lon)

            try:
                gf = check_geofence_status(sample_lat, sample_lon, db)
                if gf.get("is_inside_mpa"):
                    crosses_mpa = True
                if not gf.get("is_inside_eez"):
                    crosses_eez_border = True
            except:
                pass

            closest_cell = min(any_grid.keys(), key=lambda n: haversine_distance(sample_lat, sample_lon, n[0], n[1]))
            # Query interpolated properties at departure time
            closest_props = cls.get_interpolated_properties(closest_cell[0], closest_cell[1], t_start, loaded_grids)
            if closest_props["bsi"] >= 4:
                crosses_high_risk = True

        if crosses_mpa:
            avoided_hazards.append("Avoided Restricted MPA Sanctuaries")
        if crosses_eez_border:
            avoided_hazards.append("Avoided Border Crossings")
        if crosses_high_risk:
            avoided_hazards.append("Avoided High-Risk Wave Zone")

        if not avoided_hazards:
            avoided_hazards.append("Optimal open-water routing")

        # 8. Formulate Recommendation Summary Reason
        if shortest_path == shortest_path_b:
            recommended = "Safest & Current-Optimized Route"
            reason = "Optimal safe path. The direct route is identical."
        else:
            time_saved_min = round((total_time_b - total_time) * 60)
            extra_dist_km = round(total_distance - total_distance_b, 1)

            if max_bsi < max_bsi_b:
                recommended = "Safest & Current-Optimized Route"
                if time_saved_min > 0:
                    reason = f"{extra_dist_km} km longer, but avoids wave hazards and reduces travel time by {time_saved_min} min."
                else:
                    reason = f"{extra_dist_km} km longer to avoid capsizing hazards. Route B is faster by {abs(time_saved_min)} min but carries safety warnings."
            else:
                if time_saved_min > 0:
                    recommended = "Safest & Current-Optimized Route"
                    reason = f"{extra_dist_km} km longer, but favourable current reduces travel time by {time_saved_min} min."
                else:
                    recommended = "Shortest Direct Route"
                    reason = f"Route B is {abs(extra_dist_km)} km shorter and saves {abs(time_saved_min)} min with equal safety conditions."

        route_coords = [[node[1], node[0]] for node in shortest_path]
        alternate_route_coords = [[node[1], node[0]] for node in shortest_path_b]

        return {
            "route_coords": route_coords,
            "straight_coords": straight_coords,
            "summary": {
                "distance_km": round(total_distance, 1),
                "travel_time_hours": round(total_time, 1),
                "max_bsi": max_bsi,
                "overall_risk": overall_risk,
                "avoided_hazards": avoided_hazards
            },
            "alternate_route": {
                "route_coords": alternate_route_coords,
                "distance_km": round(total_distance_b, 1),
                "travel_time_hours": round(total_time_b, 1),
                "max_bsi": max_bsi_b,
                "overall_risk": overall_risk_b,
                "current_status": current_status_b
            },
            "comparison": {
                "recommended": recommended,
                "reason": reason
            },
            "snapshots": route_snapshots_a
        }
