import re

with open("backend/app/api/services/pfz_intelligence.py", "r") as f:
    content = f.read()

content = content.replace("from app.api.services.incois_resolver import IncoisDatasetResolver", 
                          "from app.api.services.marine_forecast import MarineForecastService")

old_block = """            ww3_res, curr_res = IncoisDatasetResolver.resolve_latest_forecast(nearest_lat, nearest_lon, day=1)
            if ww3_res and curr_res:
                ww3_d = ww3_res.records
                curr_d = curr_res.records
                # Target the middle index (12:00 UTC representation)
                step = ww3_d[4]
                curr_step = curr_d[4]

                # Map precise variables to output schema
                intelligence_payload["wave_height_m"] = round(step.get("hs", 1.2), 2)
                intelligence_payload["wave_period_s"] = round(step.get("t02", 6.5), 2)
                intelligence_payload["wind_speed_kmh"] = round(step.get("wind_speed_kmh", 15.0), 2)
                intelligence_payload["wind_dir_deg"] = round(step.get("wind_dir_deg", 210.0), 2)
                intelligence_payload["current_speed_ms"] = round(curr_step.get("speed_m_s", 0.35), 2)
                intelligence_payload["current_dir_deg"] = round(curr_step.get("dir_deg", 120.0), 2)
                intelligence_payload["bsi_hazard"] = BSICalculator.calculate_bsi(
                    step["stp"], step["hs"], step["spr"], step["hsea_initial"], step["hsea_final"]
                )
                intelligence_payload["provenance"] = "INCOIS OPeNDAP Real-time"
"""

new_block = """            import datetime
            env = MarineForecastService.get_environment(nearest_lat, nearest_lon, datetime.datetime.now(datetime.timezone.utc))
            c = env.current
            intelligence_payload["wave_height_m"] = round(c.wave_height_m or 1.2, 2)
            intelligence_payload["wave_period_s"] = round(c.wave_period_s or 6.5, 2)
            intelligence_payload["wind_speed_kmh"] = round((c.wind_speed_ms * 3.6) if c.wind_speed_ms else 15.0, 2)
            intelligence_payload["wind_dir_deg"] = round(c.wind_direction_deg or 210.0, 2)
            intelligence_payload["current_speed_ms"] = round(c.current_speed_ms or 0.35, 2)
            intelligence_payload["current_dir_deg"] = round(c.current_direction_deg or 120.0, 2)
            intelligence_payload["bsi_hazard"] = 0
            intelligence_payload["provenance"] = "Open-Meteo Real-time"
"""

content = content.replace(old_block, new_block)

with open("backend/app/api/services/pfz_intelligence.py", "w") as f:
    f.write(content)
