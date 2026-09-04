with open("backend/app/api/services/route_bsi_profiler.py", "r") as f:
    content = f.read()

old_opt = """        for hour_offset in windows:
            test_departure = base_departure + timedelta(hours=hour_offset)
            # Suppress logs for iterations to avoid spam
            profile_data = self.generate_route_profile(route_coords, vessel, test_departure)
            
            peak_sev = profile_data["route_bsi"]["maximum"]
            options.append({
                "departure_time": test_departure.isoformat(),
                "peak_severity": peak_sev,
                "mean_severity": profile_data["route_bsi"]["mean_severity"]
            })
            
            if peak_sev < lowest_peak:
                lowest_peak = peak_sev
                best_departure = test_departure"""

new_opt = """        for hour_offset in windows:
            test_departure = base_departure + timedelta(hours=hour_offset)
            profile_data = self.generate_route_profile(route_coords, vessel, test_departure)
            
            peak_sev = profile_data["route_bsi"]["maximum"]
            options.append({
                "departure_time": test_departure.isoformat(),
                "peak_severity": peak_sev,
                "mean_severity": profile_data["route_bsi"]["mean_severity"]
            })
            
            # Tie-break rule: earliest departure when multiple departures have equal minimum peak severity.
            # Using strictly less than `<` ensures that a later departure tying the lowest peak 
            # does NOT overwrite the earlier departure.
            if peak_sev < lowest_peak:
                lowest_peak = peak_sev
                best_departure = test_departure"""
content = content.replace(old_opt, new_opt)

with open("backend/app/api/services/route_bsi_profiler.py", "w") as f:
    f.write(content)
