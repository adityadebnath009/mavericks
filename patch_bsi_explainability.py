import re

with open("backend/app/api/services/orca_bsi_engine.py", "r") as f:
    content = f.read()

old_return = """        return {
            "bsi": bsi_bitmask,
            "severity_score": severity_score,
            "modifiers": {
                "vessel_susceptibility": sv,
                "heading_modifier": m_heading
            },
            "hazards": {
                "wave_steepness": steepness_data,
                "crossing_sea": crossing_data,
                "rapid_development": rapid_dev_data
            },
            "vessel": vessel.dict(),
            "environment": {
                "hs_m": hs,
                "wave_period_s": tp,
            }
        }"""

new_return = """        # Determine explicit confidence and availability
        available_hazards = ["wave_height"]
        unavailable_hazards = []
        
        if steepness_data.get("available", True) and tp > 0:
            available_hazards.append("wave_steepness")
        else:
            unavailable_hazards.append("wave_steepness")
            
        if crossing_data.get("available", False):
            available_hazards.append("crossing_sea")
        else:
            unavailable_hazards.append("crossing_sea")
            
        if rapid_dev_data.get("triggered") or rapid_dev_data.get("relative_change", 0) > 0:
            available_hazards.append("rapid_development")
        else:
            unavailable_hazards.append("rapid_development")
            
        confidence = "high" if len(unavailable_hazards) == 0 else ("partial" if len(available_hazards) >= 2 else "low")

        return {
            "bsi": bsi_bitmask,
            "severity_score": severity_score,
            "confidence": confidence,
            "available_hazards": available_hazards,
            "unavailable_hazards": unavailable_hazards,
            "modifiers": {
                "vessel_susceptibility": sv,
                "heading_modifier": m_heading
            },
            "hazards": {
                "wave_steepness": steepness_data,
                "crossing_sea": crossing_data,
                "rapid_development": rapid_dev_data
            },
            "vessel": vessel.dict(),
            "environment": {
                "hs_m": hs,
                "wave_period_s": tp,
            }
        }"""

content = content.replace(old_return, new_return)

with open("backend/app/api/services/orca_bsi_engine.py", "w") as f:
    f.write(content)
