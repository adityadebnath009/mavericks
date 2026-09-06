import time
import math
import logging
from datetime import datetime
from typing import Dict, Any, Tuple

from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions, TimelineSeries, ProvenanceRecord
from app.api.services.open_meteo_client import open_meteo_client
from app.api.services.open_meteo_provider import OpenMeteoProvider
from app.api.services.incois_geoserver import INCOISGeoServerClient

logger = logging.getLogger("marine_forecast")

class MarineForecastService:
    """
    The sole production entry point for environmental telemetry.
    No frontend component or downstream agent may directly call Open-Meteo or INCOIS for environmental telemetry.
    """
    

    _om_cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any], Dict[str, Any]]] = {}
    _sst_cache: Dict[Tuple[float, float], Tuple[float, float]] = {}

    CACHE_TTL_SECONDS = 900  # 15 minutes freshness policy

    @classmethod
    def _get_grid_key(cls, lat: float, lon: float) -> Tuple[float, float]:
        """Normalize coordinates to a 0.25 degree grid for cache spatial reuse."""
        return (round(lat * 4) / 4.0, round(lon * 4) / 4.0)

    @classmethod
    def _fetch_open_meteo_with_cache(cls, lat: float, lon: float) -> Tuple[Dict[str, Any], Dict[str, Any], bool, float]:
        """
        Fetches 72-hour forecast from Open-Meteo.
        Implements spatial (grid) and temporal (15m) caching.
        Returns: (marine_data, weather_data, is_cached, age_minutes)
        """
        grid_key = cls._get_grid_key(lat, lon)
        current_time = time.time()
        
        if grid_key in cls._om_cache:
            timestamp, marine, weather = cls._om_cache[grid_key]
            age_sec = current_time - timestamp
            if age_sec < cls.CACHE_TTL_SECONDS:
                return marine, weather, True, age_sec / 60.0
                
        # Cache Miss or Stale
        logger.info(f"Fetching fresh Open-Meteo data for grid {grid_key}")
        marine = open_meteo_client.fetch_marine_data(grid_key[0], grid_key[1])
        weather = open_meteo_client.fetch_weather_data(grid_key[0], grid_key[1])
        
        cls._om_cache[grid_key] = (current_time, marine, weather)
        return marine, weather, False, 0.0

    @classmethod
    def get_environment(cls, lat: float, lon: float, timestamp: datetime) -> EnvironmentSnapshot:
        """
        Fetches the complete EnvironmentSnapshot by orchestrating Open-Meteo and INCOIS SST.
        """
        from datetime import timezone
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            
        om_marine, om_weather, is_cached, age_minutes = cls._fetch_open_meteo_with_cache(lat, lon)
        
        # Slicing the single 72h OM response locally
        current_data, timeline_data = OpenMeteoProvider.extract_forecast(om_marine, om_weather, timestamp)
        
        # INCOIS SST & CHL Primary
        sst_value = None
        sst_fallback = False
        sst_source = "open-meteo"
        
        chl_value = None
        chl_fallback = False
        chl_source = "incois"
        
        sst_grid_key = cls._get_grid_key(lat, lon)
        current_time = time.time()
        
        if sst_grid_key in cls._sst_cache and current_time - cls._sst_cache[sst_grid_key][0] < 3600:
            sst_value, chl_value = cls._sst_cache[sst_grid_key][1], cls._sst_cache[sst_grid_key][2]
            sst_source = "incois"
        else:
            import concurrent.futures
            # Force Open-Meteo for SST immediately so we never block on it
            sst_value = current_data.get("sst_c")
            sst_source = "open-meteo"
            
            try:
                # Use a strict 2-second thread timeout so INCOIS retries don't hang the entire Telemetry API
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(INCOISGeoServerClient.get_feature_info, lat, lon, "PFZ-TUNA-SST-CHL:chl")
                    res_chl = future.result(timeout=2.0)
                    
                if res_chl.get("status") == "success" and res_chl.get("value") is not None:
                    chl_value = float(res_chl["value"])
                    
                cls._sst_cache[sst_grid_key] = (current_time, sst_value, chl_value)
            except concurrent.futures.TimeoutError:
                logger.warning(f"INCOIS fetch timed out (2s strict limit) for {lat},{lon}")
                cls._sst_cache[sst_grid_key] = (current_time, sst_value, None)
            except Exception as e:
                logger.warning(f"INCOIS fetch failed for {lat},{lon}, falling back: {e}")
                cls._sst_cache[sst_grid_key] = (current_time, sst_value, None)

        if sst_value is None:
            sst_value = current_data.get("sst_c")
            sst_fallback = True
            
        if chl_value is None:
            chl_fallback = True

        current = EnvironmentalConditions(
            timestamp=timestamp,
            wave_height_m=current_data.get("wave_height_m"),
            wave_period_s=current_data.get("wave_period_s"),
            wave_direction_deg=current_data.get("wave_direction_deg"),
            wind_wave_height_m=current_data.get("wind_wave_height_m"),
            wind_wave_period_s=current_data.get("wind_wave_period_s"),
            wind_wave_direction_deg=current_data.get("wind_wave_direction"),
            swell_wave_height_m=current_data.get("swell_wave_height"),
            swell_wave_period_s=current_data.get("swell_wave_period"),
            swell_wave_direction_deg=current_data.get("swell_wave_direction"),
            wind_speed_ms=current_data.get("wind_speed_ms"),
            wind_direction_deg=current_data.get("wind_direction_deg"),
            current_speed_ms=current_data.get("current_speed_ms"),
            current_direction_deg=current_data.get("current_direction_deg"),
            sst_c=sst_value,
            chl_mg_m3=chl_value,
            directional_spread=None
        )

        timeline = TimelineSeries(**timeline_data)

        # Build Provenance
        observed_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        provenance = {
            "wave_height_m": ProvenanceRecord(
                source="open-meteo",
                fallback=False,
                observed_at=observed_time,
                cached=is_cached,
                age_minutes=int(age_minutes)
            ),
            "wind_speed_ms": ProvenanceRecord(
                source="open-meteo",
                fallback=False,
                observed_at=observed_time,
                cached=is_cached,
                age_minutes=int(age_minutes)
            ),
            "current_speed_ms": ProvenanceRecord(
                source="open-meteo",
                fallback=False,
                observed_at=observed_time,
                cached=is_cached,
                age_minutes=int(age_minutes)
            ),
            "sst_c": ProvenanceRecord(
                source=sst_source,
                fallback=sst_fallback,
                observed_at=observed_time,
                cached=is_cached if sst_source == "open-meteo" else False,
                age_minutes=int(age_minutes) 
            ),
            "chl_mg_m3": ProvenanceRecord(
                source=chl_source,
                fallback=chl_fallback,
                observed_at=observed_time,
                cached=False,
                age_minutes=0
            ) 
        }

        return EnvironmentSnapshot(
            current=current,
            timeline=timeline,
            provenance=provenance
        )
