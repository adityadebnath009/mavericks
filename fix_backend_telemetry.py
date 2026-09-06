import re

# 1. Update Domain
f = "backend/app/core/domain.py"
with open(f, 'r') as fh: c = fh.read()
if "chl_mg_m3: Optional[float] = None" not in c:
    c = c.replace("sst_c: Optional[float] = None", "sst_c: Optional[float] = None\n    chl_mg_m3: Optional[float] = None")
with open(f, 'w') as fh: fh.write(c)

# 2. Update MarineForecastService
f = "backend/app/api/services/marine_forecast.py"
with open(f, 'r') as fh: c = fh.read()
# Add CHL fetching
replacement = """
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
            try:
                res_sst = INCOISGeoServerClient.get_feature_info(lat, lon, "PFZ-TUNA-SST-CHL:sst")
                res_chl = INCOISGeoServerClient.get_feature_info(lat, lon, "PFZ-TUNA-SST-CHL:chl")
                
                if res_sst.get("status") == "success" and res_sst.get("value") is not None:
                    sst_value = float(res_sst["value"])
                    sst_source = "incois"
                if res_chl.get("status") == "success" and res_chl.get("value") is not None:
                    chl_value = float(res_chl["value"])
                    
                if sst_value is not None or chl_value is not None:
                    cls._sst_cache[sst_grid_key] = (current_time, sst_value, chl_value)
            except Exception as e:
                logger.warning(f"INCOIS fetch failed for {lat},{lon}, falling back: {e}")

        if sst_value is None:
            sst_value = current_data.get("sst_c")
            sst_fallback = True
            
        if chl_value is None:
            chl_fallback = True
"""
c = re.sub(r'# INCOIS SST Primary.*sst_fallback = True', replacement.strip(), c, flags=re.DOTALL)
c = c.replace('sst_c=sst_value,', 'sst_c=sst_value,\n            chl_mg_m3=chl_value,')

# Add CHL provenance
provenance_replacement = """
            "sst_c": ProvenanceRecord(
                source=sst_source,
                fallback=sst_fallback,
                observed_at=observed_time,
                cached=is_cached if sst_source == "open-meteo" else False,
                age_minutes=int(age_minutes) if sst_source == "open-meteo" else 0
            ),
            "chl_mg_m3": ProvenanceRecord(
                source=chl_source,
                fallback=chl_fallback,
                observed_at=observed_time,
                cached=False,
                age_minutes=0
            )
"""
c = re.sub(r'"sst_c": ProvenanceRecord\(.*?\)', provenance_replacement.strip(), c, flags=re.DOTALL)
with open(f, 'w') as fh: fh.write(c)

# 3. Update Telemetry Endpoint
f = "backend/app/api/endpoints/telemetry.py"
with open(f, 'r') as fh: c = fh.read()
prov_repl = """
        prov = getattr(env, 'provenance', {})
        provenance = {
            "sst": {"source": prov.get("sst_c").source if "sst_c" in prov else "missing", "fallback": prov.get("sst_c").fallback if "sst_c" in prov else True},
            "chl": {"source": prov.get("chl_mg_m3").source if "chl_mg_m3" in prov else "missing", "fallback": prov.get("chl_mg_m3").fallback if "chl_mg_m3" in prov else True},
            "wave": {"source": prov.get("wave_height_m").source if "wave_height_m" in prov else "open-meteo"},
            "wind": {"source": prov.get("wind_speed_ms").source if "wind_speed_ms" in prov else "open-meteo"}
        }
"""
c = re.sub(r'provenance = {.*?}', prov_repl.strip(), c, flags=re.DOTALL)
with open(f, 'w') as fh: fh.write(c)

