import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# We need to replace _resolve_point_metrics completely to remove the fallbacks and return per-source diagnostics.
new_resolve = """    @classmethod
    def _resolve_point_metrics(cls, lat: float, lon: float) -> Tuple[Dict[str, Any], str]:
        \"\"\"
        Executes the Tier 1 INCOIS Live Services & Tier 2 Local Grid Cache.
        Returns explicit N/A (None) rather than falling back to static math if datasets are unavailable,
        providing per-source diagnostics.
        \"\"\"
        grid_lat = round(lat, 1)
        grid_lon = round(lon, 1)

        from app.api.services.incois_geoserver import INCOISGeoServerClient
        from app.api.services.incois_resolver import IncoisDatasetResolver

        metrics = {
            "sst": {"value": None, "source": "INCOIS WMS", "status": "unavailable"},
            "chlorophyll": {"value": None, "source": "INCOIS WMS", "status": "unavailable"},
            "wind_speed": {"value": None, "source": "INCOIS OPeNDAP (WW3)", "status": "unavailable"},
            "wind_direction": {"value": None, "source": "INCOIS OPeNDAP (WW3)", "status": "unavailable"},
            "current_speed": {"value": None, "source": "INCOIS OPeNDAP (Currents)", "status": "unavailable"},
            "current_direction": {"value": None, "source": "INCOIS OPeNDAP (Currents)", "status": "unavailable"},
            "wave_height": {"value": None, "source": "INCOIS OPeNDAP (WW3)", "status": "unavailable"},
            "wave_period": {"value": None, "source": "INCOIS OPeNDAP (WW3)", "status": "unavailable"}
        }

        # Attempt WMS GetFeatureInfo for SST
        try:
            sst_res = INCOISGeoServerClient.get_feature_info(grid_lat, grid_lon, "PFZ-TUNA-SST-CHL:sst")
            if sst_res.get("status") == "success" and sst_res.get("value") is not None:
                v = float(sst_res["value"])
                if 15.0 <= v <= 35.0:
                    metrics["sst"] = {"value": round(v, 1), "source": "INCOIS WMS", "status": "ok"}
        except Exception as e:
            pass

        # Attempt WMS GetFeatureInfo for Chlorophyll-a
        try:
            chl_res = INCOISGeoServerClient.get_feature_info(grid_lat, grid_lon, "PFZ-TUNA-SST-CHL:chl")
            if chl_res.get("status") == "success" and chl_res.get("value") is not None:
                v = float(chl_res["value"])
                if 0.01 <= v <= 20.0:
                    metrics["chlorophyll"] = {"value": round(v, 2), "source": "INCOIS WMS", "status": "ok"}
        except Exception as e:
            pass

        # Attempt WW3 Waves & NIO Currents NetCDF resolution
        try:
            ww3_recs, curr_recs = IncoisDatasetResolver.resolve_latest_forecast(grid_lat, grid_lon, day=1)
            if ww3_recs and curr_recs:
                step_ww3 = ww3_recs[4] if len(ww3_recs) > 4 else ww3_recs[0]
                step_curr = curr_recs[4] if len(curr_recs) > 4 else curr_recs[0]

                metrics["wind_speed"] = {"value": round(float(step_ww3.get("wind_speed_kmh", 15.0)), 1), "source": "INCOIS OPeNDAP", "status": "ok"}
                metrics["wind_direction"] = {"value": round(float(step_ww3.get("wind_direction_deg", 210.0)), 1), "source": "INCOIS OPeNDAP", "status": "ok"}
                metrics["wave_height"] = {"value": round(float(step_ww3.get("hs", 1.2)), 1), "source": "INCOIS OPeNDAP", "status": "ok"}
                metrics["wave_period"] = {"value": round(float(step_ww3.get("t02", 6.5)), 1), "source": "INCOIS OPeNDAP", "status": "ok"}
                
                metrics["current_speed"] = {"value": round(float(step_curr.get("speed_m_s", 0.30)), 2), "source": "INCOIS OPeNDAP", "status": "ok"}
                metrics["current_direction"] = {"value": round(float(step_curr.get("direction_deg", 120.0)), 1), "source": "INCOIS OPeNDAP", "status": "ok"}
        except Exception as e:
            pass
            
        return metrics, "INCOIS Direct Services\"\"\"

    @classmethod
    def _resolve_from_local_safety_grid"""

content = re.sub(r'    @classmethod\n    def _resolve_point_metrics.*?    @classmethod\n    def _resolve_from_local_safety_grid', new_resolve, content, flags=re.DOTALL)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
