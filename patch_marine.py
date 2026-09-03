import re

with open("backend/app/api/services/marine_forecast.py", "r") as f:
    content = f.read()

# Add a cache for SST
new_block = """
    _om_cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any], Dict[str, Any]]] = {}
    _sst_cache: Dict[Tuple[float, float], Tuple[float, float]] = {}
"""
content = content.replace("    _om_cache: Dict[Tuple[float, float], Tuple[float, Dict[str, Any], Dict[str, Any]]] = {}", new_block)

sst_fetch = """        # INCOIS SST Primary
        sst_value = None
        sst_fallback = False
        sst_source = "open-meteo"
        
        sst_grid_key = cls._get_grid_key(lat, lon)
        current_time = time.time()
        
        if sst_grid_key in cls._sst_cache and current_time - cls._sst_cache[sst_grid_key][0] < 3600:
            sst_value = cls._sst_cache[sst_grid_key][1]
            sst_source = "incois"
        else:
            try:
                res = INCOISGeoServerClient.get_feature_info(lat, lon, "PFZ-TUNA-SST-CHL:sst")
                if res.get("status") == "success" and res.get("value") is not None:
                    sst_value = float(res["value"])
                    sst_source = "incois"
                    cls._sst_cache[sst_grid_key] = (current_time, sst_value)
            except Exception as e:
                logger.warning(f"INCOIS SST failed for {lat},{lon}, falling back to Open-Meteo: {e}")"""

old_sst_fetch = """        # INCOIS SST Primary
        sst_value = None
        sst_fallback = False
        sst_source = "open-meteo"
        try:
            res = INCOISGeoServerClient.get_feature_info(lat, lon, "PFZ-TUNA-SST-CHL:sst")
            if res.get("status") == "success" and res.get("value") is not None:
                sst_value = float(res["value"])
                sst_source = "incois"
        except Exception as e:
            logger.warning(f"INCOIS SST failed for {lat},{lon}, falling back to Open-Meteo: {e}")"""

content = content.replace(old_sst_fetch, sst_fetch)

with open("backend/app/api/services/marine_forecast.py", "w") as f:
    f.write(content)
