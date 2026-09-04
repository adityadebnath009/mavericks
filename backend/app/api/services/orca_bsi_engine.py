import math
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.domain import EnvironmentSnapshot

logger = logging.getLogger("orca_bsi_engine")

class VesselProfile(BaseModel):
    length_m: float
    beam_m: float
    cruising_speed_kn: float
    heading_deg: Optional[float] = None

class OrcaBsiEngine:
    """
    Physics-informed, vessel-specific risk engine.
    Calculates BSI severity using deterministic wave physics and bounded modifiers.
    """
    GRAVITY = 9.81
    
    # Physics Thresholds
    STEEPNESS_THRESHOLD = 0.04       # Standard naval threshold for steep waves
    RAPID_DEV_REL_THRESHOLD = 0.30   # 30% increase in Hs is considered rapid

    @staticmethod
    def calculate_wave_steepness(hs: float, tp: float) -> Dict[str, Any]:
        """
        Calculates wave steepness: mu = (2 * pi * Hs) / (g * Tp^2)
        """
        if not hs or not tp or tp <= 0:
            return {"triggered": False, "severity": 0.0, "mu_s": 0.0}
            
        mu_s = (2 * math.pi * hs) / (OrcaBsiEngine.GRAVITY * (tp ** 2))
        triggered = mu_s > OrcaBsiEngine.STEEPNESS_THRESHOLD
        
        # Normalize severity 0.0 to 1.0 (capping at highly extreme steepness of 0.08)
        severity = min(mu_s / 0.08, 1.0)
        
        return {
            "triggered": triggered,
            "severity": round(severity, 2),
            "mu_s": round(mu_s, 4)
        }

    @staticmethod
    def calculate_vessel_susceptibility(vessel: VesselProfile) -> float:
        """
        Bounded susceptibility modifier [0.8 to 1.2].
        Baseline neutral vessel length is assumed to be 15 meters.
        """
        if not vessel or vessel.length_m <= 0:
            return 1.0
            
        # Smaller length = higher susceptibility, Larger = lower susceptibility
        base_ratio = 15.0 / vessel.length_m
        
        # Clamp strictly between 0.8 and 1.2 so it never dominates the environment
        sv = max(0.8, min(1.2, base_ratio))
        return round(sv, 2)

    @staticmethod
    def calculate_rapid_development(snapshot: EnvironmentSnapshot) -> Dict[str, Any]:
        """
        Evaluates temporal deterioration (relative change in Hs).
        Uses timeline data if available, comparing current vs historical.
        """
        if not snapshot.timeline or not snapshot.timeline.wave_height_m or len(snapshot.timeline.wave_height_m) < 2:
            return {"triggered": False, "severity": 0.0, "relative_change": 0.0}
            
        try:
            # Simple v2.1 proxy: compare current (or first) to a point ~3 hours ago
            # Assuming timeline is sequential and 1-hour intervals.
            current_hs = snapshot.wave_height_m or 0.0
            
            # Find a valid historical Hs (e.g., index 3 for T-3 hours, or last available)
            history_idx = min(3, len(snapshot.timeline.wave_height_m) - 1)
            past_hs = snapshot.timeline.wave_height_m[history_idx]
            
            if not past_hs or past_hs <= 0.1: # Prevent division by zero or noise
                return {"triggered": False, "severity": 0.0, "relative_change": 0.0}
                
            relative_change = (current_hs - past_hs) / past_hs
            triggered = relative_change > OrcaBsiEngine.RAPID_DEV_REL_THRESHOLD
            
            # Normalize severity 0.0 to 1.0 (capped at 100% increase)
            severity = max(0.0, min(relative_change / 1.0, 1.0))
            
            return {
                "triggered": triggered,
                "severity": round(severity, 2),
                "relative_change": round(relative_change, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating rapid development: {e}")
            return {"triggered": False, "severity": 0.0, "relative_change": 0.0}

    
    @staticmethod
    def calculate_wave_heading(wave_dir: Optional[float], vessel_heading: Optional[float]) -> Dict[str, Any]:
        """
        Calculates the relative wave encounter angle [0, 180].
        Beam seas (~90 deg) increase susceptibility but are not automatically dangerous.
        """
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
        """
        The ORCA crossing-sea formulation is a deterministic engineering proxy 
        informed by bimodal/crossing-sea research, not an IMO/WMO-prescribed equation.
        Calculates Bimodal Crossing Sea severity using partitioned Wind vs Swell energy.
        """
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

    def evaluate(self, snapshot: EnvironmentSnapshot, vessel: VesselProfile) -> Dict[str, Any]:
        """
        Executes the v2.1 BSI logic.
        """
        hs = snapshot.wave_height_m or 0.0
        tp = snapshot.current.wave_period_s if (snapshot.current and snapshot.current.wave_period_s is not None) else 0.0
        
        # 1. Physics Calculations
        steepness_data = self.calculate_wave_steepness(hs, tp)
        rapid_dev_data = self.calculate_rapid_development(snapshot)
        sv = self.calculate_vessel_susceptibility(vessel)
        
        crossing_data = self.calculate_crossing_seas(snapshot)
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
        
        # Environmental Severity is strictly additive, capped at 1.0. 
        # Missing hazards do not artificially dilute the score.
        env_severity_raw = min(base_hs_severity + steepness_data["severity"] + rapid_dev_data["severity"] + crossing_severity, 1.0)
        
        # 4. Independent Modifiers & Bounded Final Score
        m_heading = heading_data["modifier"]
        total_severity_raw = env_severity_raw * sv * m_heading
        severity_score = int(min(total_severity_raw * 100, 100))
        
        # Determine explicit confidence and availability
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
        }
