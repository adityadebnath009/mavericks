with open("backend/app/api/services/orca_bsi_engine.py", "r") as f:
    content = f.read()

# Replace VesselProfile
old_vessel = """class VesselProfile(BaseModel):
    length_m: float
    beam_m: float
    cruising_speed_kn: float"""

new_vessel = """class VesselProfile(BaseModel):
    length_m: float
    beam_m: float
    cruising_speed_kn: float
    heading_deg: Optional[float] = None"""
content = content.replace(old_vessel, new_vessel)

# Insert the new v2.2 methods before evaluate
eval_idx = content.find("def evaluate(self, snapshot:")

new_methods = """
    @staticmethod
    def calculate_wave_heading(wave_dir: Optional[float], vessel_heading: Optional[float]) -> Dict[str, Any]:
        \"\"\"
        Calculates the relative wave encounter angle [0, 180].
        Beam seas (~90 deg) increase susceptibility but are not automatically dangerous.
        \"\"\"
        if wave_dir is None or vessel_heading is None:
            return {"available": False, "modifier": 1.0, "relative_angle": None}
            
        angle_diff = min(abs(wave_dir - vessel_heading), 360.0 - abs(wave_dir - vessel_heading))
        
        # Modifier logic: Base 1.0. Increases up to 1.25 as it approaches 90 deg (Beam)
        # Drops back to 1.0 at 180 deg (Following)
        beam_proximity = 1.0 - (abs(angle_diff - 90.0) / 90.0)
        modifier = 1.0 + (0.25 * beam_proximity)
        
        condition = "beam" if 45 < angle_diff < 135 else "head/following"
        
        return {
            "available": True,
            "modifier": round(modifier, 2),
            "relative_angle_deg": round(angle_diff, 1),
            "condition": condition
        }

    @staticmethod
    def calculate_crossing_seas(snapshot: EnvironmentSnapshot) -> Dict[str, Any]:
        \"\"\"
        The ORCA crossing-sea formulation is a deterministic engineering proxy 
        informed by bimodal/crossing-sea research, not an IMO/WMO-prescribed equation.
        Calculates Bimodal Crossing Sea severity using partitioned Wind vs Swell energy.
        \"\"\"
        if not snapshot.current:
            return {"available": False, "triggered": False, "severity": None, "reason": "No current environment data"}
            
        ww_h = snapshot.current.wind_wave_height_m
        ww_d = snapshot.current.wind_wave_direction_deg
        sw_h = snapshot.current.swell_wave_height_m
        sw_d = snapshot.current.swell_wave_direction_deg
        
        if None in (ww_h, ww_d, sw_h, sw_d):
            return {
                "available": False,
                "triggered": False,
                "severity": None,
                "reason": "wind-sea/swell directional data unavailable"
            }
            
        ww_e = ww_h ** 2
        sw_e = sw_h ** 2
        max_e = max(ww_e, sw_e)
        
        if max_e == 0:
            return {
                "available": True, "triggered": False, "severity": 0.0,
                "method": "orca_bimodal_energy_ratio", "angular_separation_deg": 0.0, "energy_ratio": 0.0
            }
            
        energy_ratio = min(ww_e, sw_e) / max_e
        angle_diff = min(abs(ww_d - sw_d), 360.0 - abs(ww_d - sw_d))
        angular_factor = min(angle_diff, 90.0) / 90.0
        
        # Engineering Proxy
        severity = angular_factor * energy_ratio
        triggered = severity > 0.4
        
        return {
            "available": True,
            "triggered": triggered,
            "severity": round(severity, 2),
            "method": "orca_bimodal_energy_ratio",
            "angular_separation_deg": round(angle_diff, 1),
            "energy_ratio": round(energy_ratio, 2)
        }

    """

content = content[:eval_idx] + new_methods + content[eval_idx:]

# Update the evaluate method logic
old_eval_logic = """        # 2. Hazard Explainability Layer (0-7 Bitmask)
        # +1 Steepness, +2 Crossing (v2.2), +4 Rapid Development
        bsi_bitmask = 0
        if steepness_data["triggered"]:
            bsi_bitmask += 1
        # Crossing Seas is skipped in v2.1
        if rapid_dev_data["triggered"]:
            bsi_bitmask += 4
            
        # 3. Base Environmental Severity (0-100)
        # Weighting: Hs baseline + Steepness + Rapid Dev
        # Baseline Hs severity (normalized to max 4m for this proxy)
        base_hs_severity = min(hs / 4.0, 1.0)
        
        # Composite environmental severity (average of available hazards + base)
        env_severity_raw = (base_hs_severity + steepness_data["severity"] + rapid_dev_data["severity"]) / 3.0
        
        # 4. Total Severity (Vessel Modified)
        total_severity_raw = env_severity_raw * sv
        severity_score = int(min(total_severity_raw * 100, 100))
        
        return {
            "bsi": bsi_bitmask,
            "severity_score": severity_score,
            "hazards": {
                "wave_steepness": steepness_data,
                "crossing_sea": {
                    "available": False,
                    "severity": None,
                    "reason": "crossing_sea logic slated for v2.2"
                },
                "rapid_development": rapid_dev_data
            },
            "vessel": vessel.dict(),
            "environment": {
                "hs_m": hs,
                "wave_period_s": tp,
            }
        }"""

new_eval_logic = """        crossing_data = self.calculate_crossing_seas(snapshot)
        heading_data = self.calculate_wave_heading(snapshot.current.wave_direction_deg if snapshot.current else None, vessel.heading_deg)
        
        # 2. Hazard Explainability Layer (0-7 Bitmask)
        # +1 Steepness, +2 Crossing, +4 Rapid Development
        bsi_bitmask = 0
        if steepness_data.get("triggered"):
            bsi_bitmask += 1
        if crossing_data.get("triggered"):
            bsi_bitmask += 2
        if rapid_dev_data.get("triggered"):
            bsi_bitmask += 4
            
        # 3. Environmental Severity (0-100 Base)
        # Keeping components independently visible
        base_hs_severity = min(hs / 4.0, 1.0)
        crossing_severity = crossing_data.get("severity", 0.0) or 0.0
        
        env_severity_raw = (base_hs_severity + steepness_data["severity"] + rapid_dev_data["severity"] + crossing_severity) / 4.0
        
        # 4. Independent Modifiers & Bounded Final Score
        m_heading = heading_data["modifier"]
        total_severity_raw = env_severity_raw * sv * m_heading
        severity_score = int(min(total_severity_raw * 100, 100))
        
        return {
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
content = content.replace(old_eval_logic, new_eval_logic)

with open("backend/app/api/services/orca_bsi_engine.py", "w") as f:
    f.write(content)
