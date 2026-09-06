import sys

with open('backend/app/api/services/pfz_intelligence.py', 'r') as f:
    content = f.read()

# Replace imports
content = content.replace("from app.api.services.incois_resolver import IncoisDatasetResolver", "from app.api.services.marine_forecast import MarineForecastService\nfrom app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile\nimport datetime")
content = content.replace("from app.api.services.bsi_calculator import BSICalculator", "")

# We need to replace the entire try-except block starting around line 76 to 127
old_block = """        try:
            # Query INCOIS OPeNDAP forecast for Day 1 at the closest PFZ coordinate
            ww3_res, curr_res = IncoisDatasetResolver.resolve_latest_forecast(nearest_lat, nearest_lon, day=1)
            if ww3_res and curr_res:
                ww3_d = ww3_res.records
                curr_d = curr_res.records
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
                pass"""

new_block = """        target_date = datetime.datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
        try:
            snapshot = MarineForecastService.get_environment(nearest_lat, nearest_lon, target_date)
            vessel = VesselProfile(length_m=15.0, beam_m=beam_m, cruising_speed_kn=10.0)
            orca_result = OrcaBsiEngine().evaluate(snapshot, vessel)
            bsi = orca_result["severity_score"]
            
            hs = snapshot.current.wave_height_m or 1.2
            wind_speed = (snapshot.current.wind_speed_ms * 3.6) if snapshot.current.wind_speed_ms else 15.0
            current_speed = snapshot.current.current_speed_ms or 0.25
            stp = snapshot.current.directional_spread or 0.015
            spr = snapshot.current.directional_spread or 0.25
            source = "MarineForecastService (B2)"
        except Exception as e:
            logger.warning(f"MarineForecastService failed for {nearest_lat},{nearest_lon}: {e}")"""

content = content.replace(old_block, new_block)

old_bsi_logic = """        # BSI Risk
        if bsi >= 4:
            bsi_risk = "HIGH"
            reasons.append("High capsizing risk (BSI score >= 4)")
        elif bsi >= 2:
            bsi_risk = "MODERATE"
            reasons.append("Moderate capsizing/crossing sea risk (BSI score >= 2)")
        else:
            bsi_risk = "LOW\""""

new_bsi_logic = """        # BSI Risk
        if bsi >= 76:
            bsi_risk = "HIGH"
            reasons.append(f"High capsizing risk (BSI score {bsi})")
        elif bsi >= 21:
            bsi_risk = "MODERATE"
            reasons.append(f"Moderate capsizing/crossing sea risk (BSI score {bsi})")
        else:
            bsi_risk = "LOW\""""

content = content.replace(old_bsi_logic, new_bsi_logic)

with open('backend/app/api/services/pfz_intelligence.py', 'w') as f:
    f.write(content)
