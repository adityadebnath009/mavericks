import math
import logging
from shapely.geometry import Point, shape
from shapely.ops import nearest_points
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.incois_resolver import IncoisDatasetResolver
from app.api.services.bsi_calculator import BSICalculator

logger = logging.getLogger(__name__)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Computes distance between two coordinates in kilometers using the Haversine formula.
    """
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class PFZIntelligenceService:
    """
    Service for calculating proximity and localized meteorological/oceanographic risks
    for official INCOIS Potential Fishing Zones (PFZs) retrieved via WFS.
    """

    @classmethod
    def evaluate_pfz_zone(cls, vessel_lat: float, vessel_lon: float, pfz_id: str, beam_m: float = 3.5) -> dict:
        """
        Locates the specified WFS PFZ line, calculates the nearest coordinate on that line
        to the vessel, and evaluates the independent safety risks at that nearest coordinate.
        """
        # 1. Fetch PFZ lines GeoJSON from INCOIS WFS (or cache)
        geojson_data = INCOISGeoServerClient.get_pfz_lines_wfs()
        target_feature = None

        for feat in geojson_data.get("features", []):
            if feat.get("id") == pfz_id:
                target_feature = feat
                break

        if not target_feature:
            raise ValueError(f"PFZ Advisory feature with ID '{pfz_id}' not found.")

        # 2. Parse geometry and find closest point to the vessel
        geom = shape(target_feature["geometry"])
        vessel_pt = Point(vessel_lon, vessel_lat)
        nearest_geom_pt, _ = nearest_points(geom, vessel_pt)
        nearest_lat = nearest_geom_pt.y
        nearest_lon = nearest_geom_pt.x

        # Calculate Haversine distance
        dist_km = haversine_distance(vessel_lat, vessel_lon, nearest_lat, nearest_lon)

        # 3. Retrieve meteorological conditions at the nearest coordinate
        # Default fallback values in case resolver fails
        hs = 1.2
        wind_speed = 15.0
        current_speed = 0.25
        stp = 0.015
        spr = 0.25
        hsea_initial = 0.8
        hsea_final = 0.8
        bsi = 0
        source = "Open-Meteo (Fallback)"

        try:
            # Query INCOIS OPeNDAP forecast for Day 1 at the closest PFZ coordinate
            ww3_d, curr_d = IncoisDatasetResolver.resolve_latest_forecast(nearest_lat, nearest_lon, day=1)
            if ww3_d and curr_d:
                # Target the middle index (12:00 UTC representation)
                step = ww3_d[4]
                hs = step["hs"]
                wind_speed = step["wind_speed_kmh"]
                stp = step["stp"]
                spr = step["spr"]
                hsea_initial = step["hsea_initial"]
                hsea_final = step["hsea_final"]
                current_speed = curr_d[4]["speed_m_s"]
                bsi = BSICalculator.calculate_bsi(stp, hs, spr, hsea_initial, hsea_final)
                source = "INCOIS OPENDAP"
        except Exception as e:
            logger.warning(f"Resolver failed for PFZ coordinate {nearest_lat},{nearest_lon}, using Open-Meteo fallback: {e}")
            # Try to fetch from Open-Meteo as tertiary fallback
            try:
                from app.api.endpoints.weather import get_marine_weather
                weather = get_marine_weather(nearest_lat, nearest_lon)
                forecast = weather.get("forecast_hourly", {})
                hs = sum(forecast.get("wave_height_m", [1.2])[:24]) / 24.0
                wind_speed = sum(forecast.get("wind_speed_kmh", [15.0])[:24]) / 24.0
                current_speed = 0.1 + hs * 0.18
                bsi = 1 if hs > 1.25 else 0
            except:
                pass

        # 4. Classify Marine Risk independently from the PFZ presence
        reasons = []
        rating = "LOW"

        # Wind Risk
        if wind_speed >= 40.0:
            wind_risk = "HIGH"
            reasons.append(f"Extreme wind speed ({wind_speed:.1f} km/h)")
        elif wind_speed >= 25.0:
            wind_risk = "MODERATE"
            reasons.append(f"Elevated wind speed ({wind_speed:.1f} km/h)")
        else:
            wind_risk = "LOW"

        # Current Risk
        if current_speed >= 1.2:
            curr_risk = "HIGH"
            reasons.append(f"Extreme current speed ({current_speed:.2f} m/s)")
        elif current_speed >= 0.5:
            curr_risk = "MODERATE"
            reasons.append(f"Moderate current speed ({current_speed:.2f} m/s)")
        else:
            curr_risk = "LOW"

        # BSI Risk
        if bsi >= 4:
            bsi_risk = "HIGH"
            reasons.append("High capsizing risk (BSI score >= 4)")
        elif bsi >= 2:
            bsi_risk = "MODERATE"
            reasons.append("Moderate capsizing/crossing sea risk (BSI score >= 2)")
        else:
            bsi_risk = "LOW"

        # Wave height vs. Vessel Beam capsize floor
        critical_height = 1.5 * beam_m
        if hs >= critical_height:
            reasons.append(f"Significant wave height ({hs:.2f}m) exceeds vessel stability limit ({critical_height:.2f}m)")
            rating = "HIGH"

        # Compute overall Marine Risk rating
        if "HIGH" in [wind_risk, curr_risk, bsi_risk] or rating == "HIGH":
            rating = "HIGH"
        elif "MODERATE" in [wind_risk, curr_risk, bsi_risk]:
            rating = "MODERATE"

        if not reasons:
            reasons.append("Optimal weather, wave, and current parameters at the zone.")

        return {
            "pfz_id": pfz_id,
            "distance_km": round(dist_km, 2),
            "nearest_point": {
                "latitude": round(nearest_lat, 4),
                "longitude": round(nearest_lon, 4)
            },
            "properties": target_feature.get("properties", {}),
            "marine_conditions": {
                "wave_height_m": round(hs, 2),
                "wind_speed_kmh": round(wind_speed, 1),
                "current_speed_ms": round(current_speed, 2),
                "wave_steepness": round(stp, 4),
                "directional_spread": round(spr, 2)
            },
            "marine_risk": {
                "rating": rating,
                "reasons": reasons
            },
            "provenance": {
                "source": source,
                "dataset_resolution": "0.4 degrees (~44 km)"
            }
        }
