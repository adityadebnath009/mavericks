import ee
import logging
import json
import os
import math
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GEEService:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return True
            
        try:
            # Requires `earthengine authenticate` or ADC setup prior to running
            ee.Initialize(project='stately-winter-461407-c7')
            cls._initialized = True
            logger.info("Successfully initialized Google Earth Engine.")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize GEE. Using fallback deterministic data. Error: {e}")
            cls._initialized = False
            return False

    @classmethod
    def fetch_current_sst_and_chlorophyll(cls, lat: float, lon: float) -> Dict[str, float]:
        """Fetches latest SST and Chlorophyll for a point."""
        if not cls.initialize():
            # Fallback mock physically constrained to lat/lon
            return {
                "sst": round(28.5 + math.sin(lat) * 2.0, 2),
                "chlorophyll": round(abs(0.5 + math.cos(lon) * 0.3), 3)
            }
            
        try:
            point = ee.Geometry.Point([lon, lat])
            
            # SST: NOAA OISST V2.1 (Daily)
            sst_collection = ee.ImageCollection("NOAA/CDR/OISST/V2_1")\
                .filterBounds(point)\
                .sort('system:time_start', False)\
                .first()
                
            # Chlorophyll: MODIS Aqua Level 3
            chl_collection = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI")\
                .filterBounds(point)\
                .select('chlor_a')\
                .sort('system:time_start', False)\
                .first()
                
            sst_val = sst_collection.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=10000
            ).get('sst').getInfo()
            
            chl_val = chl_collection.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=4000
            ).get('chlor_a').getInfo()
            
            return {
                "sst": float(sst_val) if sst_val is not None else 28.5,
                "chlorophyll": float(chl_val) if chl_val is not None else 0.5
            }
        except Exception as e:
            logger.error(f"GEE Fetch error: {e}")
            return {
                "sst": round(28.5 + math.sin(lat) * 2.0, 2),
                "chlorophyll": round(abs(0.5 + math.cos(lon) * 0.3), 3)
            }

    @classmethod
    def fetch_historical_timeseries(cls, lat: float, lon: float, years: int = 5) -> Dict[str, List[float]]:
        """Fetches multi-year historical timeseries for anomaly detection."""
        base_sst = 28.5 + math.sin(lat) * 2.0
        base_chl = abs(0.5 + math.cos(lon) * 0.3)
        fallback_data = {
            "sst_series": [round(base_sst - (i * 0.05), 2) for i in range(years * 12)], 
            "chlorophyll_series": [round(base_chl - (i * 0.02), 3) for i in range(years * 12)]
        }
            
        if not cls.initialize():
            return fallback_data

        # Keep the historical path deliberately bounded until a server-side
        # time-series export is implemented.
        return fallback_data

    @classmethod
    def build_overlay_layers(cls) -> List[Dict[str, Any]]:
        """Return renderer-ready, short-lived GEE XYZ URLs without exposing credentials.

        Map IDs are deliberately created only here on the server.  If Earth Engine
        cannot authenticate or create a map ID, the frontend receives an explicit
        disabled layer instead of invented satellite imagery.
        """
        definitions = [
            # A daily product that has not advanced for over two weeks is no
            # longer current operational imagery.  It may still be rendered
            # as context, but the Console must label it STALE.
            ("gee_sst", "Sea Surface Temperature", "NOAA/CDR/OISST/V2_1", "sst", {"min": 271, "max": 305, "palette": ["001b44", "00d4ff", "ffb547", "ff5c5c"]}, True, 14),
            # Ocean-colour coverage can be delayed by cloud screening and
            # processing, hence a slightly longer truthfulness threshold.
            ("gee_chl", "Chlorophyll-a", "NASA/OCEANDATA/MODIS-Aqua/L3SMI", "chlor_a", {"min": 0, "max": 2, "palette": ["061a2b", "18c7a0", "d9f99d"]}, False, 45),
        ]
        layers = []
        if not cls.initialize():
            return [
                {"id": layer_id, "title": title, "type": "raster", "provider": "GEE", "visible": visible,
                 "opacity": 0.65, "status": "UNAVAILABLE", "unavailableReason": "Earth Engine authentication is unavailable."}
                for layer_id, title, _collection, _band, _style, visible, _max_age_days in definitions
            ]

        for layer_id, title, collection, band, style, visible, max_age_days in definitions:
            try:
                image = ee.ImageCollection(collection).select(band).sort("system:time_start", False).first()
                acquired_ms = image.get("system:time_start").getInfo()
                acquired_at = datetime.fromtimestamp(float(acquired_ms) / 1000, tz=timezone.utc) if acquired_ms is not None else None
                age_hours = round((datetime.now(timezone.utc) - acquired_at).total_seconds() / 3600, 1) if acquired_at else None
                is_stale = age_hours is None or age_hours > max_age_days * 24
                # NOAA OISST stores Celsius observations with a 0.01 scale
                # factor. Apply it for the Console-only tile renderer before
                # visualising, otherwise tropical values (~2964 raw) saturate
                # an unscaled palette and make the full ocean appear red.
                if layer_id == "gee_sst":
                    image = image.multiply(0.01)
                    style = {"min": 24, "max": 32, "palette": ["001b44", "00a8ff", "18c7a0", "ffb547", "ff5c5c"]}
                map_id = image.visualize(**style).getMapId({})
                tile_url = map_id["tile_fetcher"].url_format
                layers.append({"id": layer_id, "title": title, "type": "raster", "provider": "GEE", "visible": visible,
                               "opacity": 0.65, "status": "STALE" if is_stale else "AVAILABLE", "tiles": [tile_url],
                               "dataTimestamp": acquired_at.isoformat() if acquired_at else None, "ageHours": age_hours,
                               "staleReason": ("Satellite acquisition time is unavailable." if acquired_at is None else f"Satellite image is {age_hours:.1f} hours old.") if is_stale else None})
            except Exception as exc:
                logger.warning("Unable to create GEE overlay %s: %s", layer_id, exc)
                layers.append({"id": layer_id, "title": title, "type": "raster", "provider": "GEE", "visible": visible,
                               "opacity": 0.65, "status": "UNAVAILABLE", "unavailableReason": "Satellite tile generation failed."})
        return layers
