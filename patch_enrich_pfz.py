import re
with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Replace enrich_pfz extraction logic
old_extraction = """        for p_lat, p_lon in sampled_coords:
            point_data = cls.enrich_point(p_lat, p_lon, timestamp=iso_timestamp)
            m = point_data.get("metrics", {})
            sst_list.append(float(m.get("sst_c", 28.4)))
            chl_list.append(float(m.get("chl_mg_m3", 0.45)))
            wave_list.append(float(m.get("wave_height_m", 1.2)))
            curr_list.append(float(m.get("current_speed_ms", 0.35)))
            wind_list.append(float(m.get("wind_speed_kmh", 16.2)))
            sources.append(point_data.get("source", "INCOIS Telemetry"))

        # 5. Compute Statistical Medians
        sst_median = round(float(statistics.median(sst_list)), 1)
        chl_median = round(float(statistics.median(chl_list)), 2)
        wave_hs_median = round(float(statistics.median(wave_list)), 1)
        current_median = round(float(statistics.median(curr_list)), 2)
        wind_speed_median = round(float(statistics.median(wind_list)), 1)"""

new_extraction = """        for p_lat, p_lon in sampled_coords:
            point_data = cls.enrich_point(p_lat, p_lon, timestamp=iso_timestamp)
            m = point_data.get("metrics", {})
            
            # Helper to extract value from nested diagnostic schema
            def get_val(key):
                v = m.get(key)
                if isinstance(v, dict):
                    return v.get("value")
                return v

            sst_val = get_val("sst")
            if sst_val is not None: sst_list.append(float(sst_val))
            
            chl_val = get_val("chlorophyll")
            if chl_val is not None: chl_list.append(float(chl_val))
            
            wave_val = get_val("wave_height")
            if wave_val is not None: wave_list.append(float(wave_val))
            
            curr_val = get_val("current_speed")
            if curr_val is not None: curr_list.append(float(curr_val))
            
            wind_val = get_val("wind_speed")
            if wind_val is not None: wind_list.append(float(wind_val))
            
            sources.append(point_data.get("source", "INCOIS Telemetry"))

        # 5. Compute Statistical Medians (Handle Empty Lists Gracefully)
        sst_median = round(float(statistics.median(sst_list)), 1) if sst_list else None
        chl_median = round(float(statistics.median(chl_list)), 2) if chl_list else None
        wave_hs_median = round(float(statistics.median(wave_list)), 1) if wave_list else None
        current_median = round(float(statistics.median(curr_list)), 2) if curr_list else None
        wind_speed_median = round(float(statistics.median(wind_list)), 1) if wind_list else None"""

content = content.replace(old_extraction, new_extraction)

# Now we also need to fix catch_score to not crash if any median is None
old_score = """        catch_score = cls.calculate_catch_score(
            sst_median=sst_median,
            chl_median=chl_median,
            wave_hs_median=wave_hs_median,
            current_median=current_median,
            wind_speed_median=wind_speed_median
        )"""

new_score = """        try:
            catch_score = cls.calculate_catch_score(
                sst_median=sst_median if sst_median is not None else 28.4,
                chl_median=chl_median if chl_median is not None else 0.45,
                wave_hs_median=wave_hs_median if wave_hs_median is not None else 1.2,
                current_median=current_median if current_median is not None else 0.35,
                wind_speed_median=wind_speed_median if wind_speed_median is not None else 16.2
            )
        except Exception:
            catch_score = 40"""

content = content.replace(old_score, new_score)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
