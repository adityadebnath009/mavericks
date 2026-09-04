with open("backend/app/api/services/route_bsi_profiler.py", "r") as f:
    content = f.read()

# 1. Update invalid speed handling
old_eta = """        speed_kmh = vessel.cruising_speed_kn * 1.852
        if speed_kmh <= 0:
            speed_kmh = 10.0 # safe fallback"""
            
new_eta = """        if vessel.cruising_speed_kn <= 0:
            raise ValueError("Vessel cruising speed must be strictly positive.")
        speed_kmh = vessel.cruising_speed_kn * 1.852"""
content = content.replace(old_eta, new_eta)

# 2. Update Duration calculation
old_eval = """        for node in profile_nodes:
            grid_key = f"{round(node['lat'], 1)}_{round(node['lon'], 1)}"
            env_timeline = unique_grids[grid_key]
            
            # v2.3-B: Temporal Slicing (extract conditions exactly at node['eta'])
            # We mock time-slicing logic by passing the ETA to the snapshot generator
            # (In production, the marine service extracts the exact hour index from the 72h cache)
            snapshot_at_eta = env_timeline.get_slice_at(node["eta"]) if hasattr(env_timeline, 'get_slice_at') else env_timeline
            
            bsi_result = self.bsi_engine.evaluate(snapshot_at_eta, vessel)
            
            node_severity = bsi_result["severity_score"]
            node_bsi = bsi_result["bsi"]
            
            # Aggregation logic
            sum_severity += node_severity
            if node_bsi > max_bsi or (node_bsi == max_bsi and node_severity > (evaluated_profile[peak_node]["severity"] if evaluated_profile else 0)):
                max_bsi = node_bsi
                peak_node = node["node_idx"]
                peak_eta = node["eta"]
                
            if node_severity >= 60: # 60+ is considered high severity
                high_severity_count += 1
                
            evaluated_profile.append({
                "node": node["node_idx"],
                "lat": node["lat"],
                "lon": node["lon"],
                "eta": node["eta"],
                "bsi": node_bsi,
                "severity": node_severity
            })
            
        mean_severity = sum_severity / len(evaluated_profile)
        
        # Calculate duration in high severity (approx based on node spacing)
        # For simplicity in v2.3, treat each node as a fraction of total time
        total_trip_hours = (profile_nodes[-1]["eta"] - profile_nodes[0]["eta"]).total_seconds() / 3600.0
        high_risk_duration = (high_severity_count / len(evaluated_profile)) * total_trip_hours"""

new_eval = """        high_risk_duration_seconds = 0.0
        
        for i, node in enumerate(profile_nodes):
            grid_key = f"{round(node['lat'], 1)}_{round(node['lon'], 1)}"
            env_timeline = unique_grids[grid_key]
            
            # Temporal Slicing (extract conditions exactly at node['eta'])
            snapshot_at_eta = env_timeline.get_slice_at(node["eta"]) if hasattr(env_timeline, 'get_slice_at') else env_timeline
            
            bsi_result = self.bsi_engine.evaluate(snapshot_at_eta, vessel)
            
            node_severity = bsi_result["severity_score"]
            node_bsi = bsi_result["bsi"]
            
            # Aggregation logic
            sum_severity += node_severity
            if node_bsi > max_bsi or (node_bsi == max_bsi and (not evaluated_profile or node_severity > evaluated_profile[peak_node]["severity"])):
                max_bsi = node_bsi
                peak_node = node["node_idx"]
                peak_eta = node["eta"]
                
            if node_severity >= 60: 
                # Accurate duration: use the time delta from previous node
                if i > 0:
                    delta_sec = (node["eta"] - profile_nodes[i-1]["eta"]).total_seconds()
                    high_risk_duration_seconds += delta_sec
                else:
                    # If start node is high severity, assume it applies to half the next leg to be conservative
                    if len(profile_nodes) > 1:
                        high_risk_duration_seconds += (profile_nodes[1]["eta"] - node["eta"]).total_seconds() / 2.0
                
            evaluated_profile.append({
                "node": node["node_idx"],
                "lat": node["lat"],
                "lon": node["lon"],
                "eta": node["eta"],
                "bsi": node_bsi,
                "severity": node_severity
            })
            
        mean_severity = sum_severity / len(evaluated_profile)
        high_risk_duration = high_risk_duration_seconds / 3600.0"""
        
content = content.replace(old_eval, new_eval)

# Fix isoformat in peak_eta since we want to return a clean string
old_ret = """        return {
            "route_bsi": {
                "current": evaluated_profile[0]["bsi"],
                "maximum": max_bsi,
                "mean_severity": round(mean_severity, 1),
                "peak_node": peak_node,
                "peak_eta": peak_eta.isoformat(),
                "high_severity_duration_hours": round(high_risk_duration, 1)
            },
            "profile": evaluated_profile
        }"""
        
new_ret = """        # Convert ETAs to isoformat for API output
        peak_eta_iso = peak_eta.isoformat() if isinstance(peak_eta, datetime) else peak_eta
        for p in evaluated_profile:
            if isinstance(p["eta"], datetime):
                p["eta"] = p["eta"].isoformat()
                
        return {
            "route_bsi": {
                "current": evaluated_profile[0]["bsi"],
                "maximum": max_bsi,
                "mean_severity": round(mean_severity, 1),
                "peak_node": peak_node,
                "peak_eta": peak_eta_iso,
                "high_severity_duration_hours": round(high_risk_duration, 1)
            },
            "profile": evaluated_profile
        }"""
        
content = content.replace(old_ret, new_ret)

with open("backend/app/api/services/route_bsi_profiler.py", "w") as f:
    f.write(content)
