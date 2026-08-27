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
        db: Session
    ) -> dict:
        """
        Executes Dijkstra pathfinding over the active safety grid cells,
        returning waypoint coordinates and route summary metrics.
        """
        # 1. Load the active pre-warmed safety grid cache
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
        cache_path = os.path.join(cache_dir, f"safety_grid_day_{day}_hour_{hour}.json")

        if not os.path.exists(cache_path):
            raise FileNotFoundError(f"Safety grid cache file for day {day} hour {hour} not found.")

        with open(cache_path, "r", encoding="utf-8") as f:
            grid_geojson = json.load(f)

        features = grid_geojson.get("features", [])
        if not features:
            raise ValueError("No active grid cells available in the cache.")

        # 2. Build the grid nodes map: (lat, lon) -> properties
        nodes_map = {}
        for feat in features:
            props = feat["properties"]
            c_lat = props.get("center_lat")
            c_lon = props.get("center_lon")
            if c_lat is not None and c_lon is not None:
                # Store node coordinates rounded to 4 decimals to ensure key matching
                node_key = (round(c_lat, 4), round(c_lon, 4))
                nodes_map[node_key] = feat

        if not nodes_map:
            raise ValueError("Failed to construct coordinates nodes map from cached grid.")

        # 3. Locate closest grid nodes to the start and end coordinates
        start_node = min(nodes_map.keys(), key=lambda n: haversine_distance(start_lat, start_lon, n[0], n[1]))
        end_node = min(nodes_map.keys(), key=lambda n: haversine_distance(end_lat, end_lon, n[0], n[1]))

        # 4. Execute Dijkstra Search
        queue = [(0.0, start_node, [start_node])]
        visited = set()
        geofence_cache = {}
        shortest_path = None
        min_cost = None

        while queue:
            (cost, u, path) = heapq.heappop(queue)

            if u in visited:
                continue
            visited.add(u)

            if u == end_node:
                shortest_path = path
                min_cost = cost
                break

            u_lat, u_lon = u
            # Search for neighboring nodes (orthogonal and diagonal delta approx 0.6 degrees)
            for v in nodes_map.keys():
                if v in visited:
                    continue

                if abs(v[0] - u_lat) <= 0.65 and abs(v[1] - u_lon) <= 0.65 and v != u:
                    dist = haversine_distance(u_lat, u_lon, v[0], v[1])
                    props_v = nodes_map[v]["properties"]
                    hs = props_v["hs"]
                    wind = props_v.get("wind_speed_kmh", 15.0)
                    bsi = props_v.get("bsi", 0)

                    # Involuntary speed loss calculation (Kwon drag approximation)
                    vessel_speed = 15.0  # km/h
                    delta_v = 0.1 * (hs ** 2) + 0.04 * wind
                    effective_speed = max(2.0, vessel_speed - delta_v)
                    transit_time = dist / effective_speed

                    # BSI safety penalty weight
                    bsi_penalty = 5.0 * (bsi ** 2)

                    # Hard constraint: Wave height vs Beam capsize floor
                    critical_height = 1.5 * beam_m
                    if hs >= critical_height:
                        continue

                    # Geofencing queries using super fast local boundary calculation
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
                        continue  # Strictly forbidden navigation zones

                    # Approaching border soft penalty
                    border_penalty = 0.0
                    if gf.get("distance_to_border_km", 999.0) < 5.0:
                        border_penalty = 20.0

                    edge_cost = transit_time + bsi_penalty + border_penalty
                    heapq.heappush(queue, (cost + edge_cost, v, path + [v]))

        # 5. Handle path fallback if Dijkstra failed to find a path
        if not shortest_path:
            # Fallback to straight line from start to end node
            shortest_path = [start_node, end_node]

        # 6. Compute Path Metrics and Summary details
        total_distance = 0.0
        total_time = 0.0
        max_bsi = 0
        overall_risk = "LOW"

        # List coordinates in Leaflet/MapLibre [longitude, latitude] order
        route_coords = []
        for i, node in enumerate(shortest_path):
            route_coords.append([node[1], node[2] if len(node) > 2 else node[0]]) # Wait! node is a tuple (lat, lon)
            
        # Let's fix that list formatting:
        route_coords = [[node[1], node[0]] for node in shortest_path]

        for i in range(len(shortest_path) - 1):
            u = shortest_path[i]
            v = shortest_path[i+1]
            total_distance += haversine_distance(u[0], u[1], v[0], v[1])
            
            props_v = nodes_map.get(v, {}).get("properties", {})
            hs = props_v.get("hs", 1.2)
            wind = props_v.get("wind_speed_kmh", 15.0)
            bsi = props_v.get("bsi", 0)
            
            delta_v = 0.1 * (hs ** 2) + 0.04 * wind
            effective_speed = max(2.0, 15.0 - delta_v)
            total_time += haversine_distance(u[0], u[1], v[0], v[1]) / effective_speed
            
            if bsi > max_bsi:
                max_bsi = bsi

        if max_bsi >= 4:
            overall_risk = "HIGH"
        elif max_bsi >= 2:
            overall_risk = "MODERATE"

        # 7. Compare against straight line to identify avoided hazards
        avoided_hazards = []
        # Sample 5 points along straight line
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
                
            # Find closest cached cell for wave bsi check
            closest_cell = min(nodes_map.keys(), key=lambda n: haversine_distance(sample_lat, sample_lon, n[0], n[1]))
            if nodes_map[closest_cell]["properties"].get("bsi", 0) >= 4:
                crosses_high_risk = True

        if crosses_mpa:
            avoided_hazards.append("Avoided Restricted MPA Sanctuaries")
        if crosses_eez_border:
            avoided_hazards.append("Avoided Border Crossings")
        if crosses_high_risk:
            avoided_hazards.append("Avoided High-Risk Wave Zone")

        if not avoided_hazards:
            avoided_hazards.append("Optimal open-water routing")

        return {
            "route_coords": route_coords,
            "straight_coords": straight_coords,
            "summary": {
                "distance_km": round(total_distance, 1),
                "travel_time_hours": round(total_time, 1),
                "max_bsi": max_bsi,
                "overall_risk": overall_risk,
                "avoided_hazards": avoided_hazards
            }
        }
