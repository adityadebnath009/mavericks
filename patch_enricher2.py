import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

start_idx = content.find("def _resolve_point_metrics")
end_idx = content.find("def _resolve_from_local_safety_grid")

if start_idx != -1 and end_idx != -1:
    new_func = """def _resolve_point_metrics(cls, lat: float, lon: float, shutdown_event=None) -> Tuple[Dict[str, Any], str]:
        from app.api.services.marine_forecast import MarineForecastService
        from app.api.services.incois_geoserver import INCOISGeoServerClient
        import datetime
        
        if shutdown_event and shutdown_event.is_set(): raise InterruptedError("Shutdown")
        
        env = MarineForecastService.get_environment(lat, lon, datetime.datetime.now(datetime.timezone.utc))
        
        if shutdown_event and shutdown_event.is_set(): raise InterruptedError("Shutdown")
        
        chl_val = None
        try:
            chl_res = INCOISGeoServerClient.get_feature_info(round(lat, 1), round(lon, 1), "PFZ-TUNA-SST-CHL:chl")
            if chl_res.get("status") == "success" and chl_res.get("value") is not None:
                v = float(chl_res["value"])
                if 0.01 <= v <= 20.0:
                    chl_val = round(v, 2)
        except Exception: pass
        
        c = env.current
        p = env.provenance
        
        def format_metric(val, name):
            if val is None:
                src = p.get(name).source if name in p else "Unknown"
                return {"value": None, "source": src, "status": "unavailable"}
            src = p.get(name).source if name in p else "open-meteo"
            return {"value": round(val, 2), "source": src, "status": "ok"}
            
        metrics = {
            "sst": format_metric(c.sst_c, "sst_c"),
            "chlorophyll": {"value": chl_val, "source": "INCOIS WMS", "status": "ok" if chl_val else "unavailable"},
            "wind_speed": format_metric(c.wind_speed_ms * 3.6 if c.wind_speed_ms is not None else None, "wind_speed_ms"),
            "wind_direction": format_metric(c.wind_direction_deg, "wind_speed_ms"),
            "current_speed": format_metric(c.current_speed_ms, "current_speed_ms"),
            "current_direction": format_metric(c.current_direction_deg, "current_speed_ms"),
            "wave_height": format_metric(c.wave_height_m, "wave_height_m"),
            "wave_period": format_metric(c.wave_period_s, "wave_height_m")
        }
        
        return metrics, "Live Services (OM+INCOIS)"

    @classmethod
    """
    
    content = content[:start_idx] + new_func + content[end_idx:]

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
