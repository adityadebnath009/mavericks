from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Evidence Ontology ---
class EvidenceOntology:
    TEMPORAL = ["current_conditions", "historical_series", "forecast_window"]
    FISHERIES = ["pfz_candidates", "pfz_coordinates", "chlorophyll", "sst", "fishing_opportunity", "distance_from_reference"]
    SAFETY = ["wave_height", "wave_period", "swell", "wind", "marine_warnings", "marine_severity", "tide_level"]
    ROUTING = ["route_path", "travel_time", "marine_severity", "geofence_status", "restricted_zone_status", "route_start_time", "estimated_arrival_time"]
    RESEARCH = ["productivity", "sst_series", "chlorophyll_series", "fishing_effort", "correlation", "literature_evidence"]
    
    @classmethod
    def all_keys(cls):
        return cls.TEMPORAL + cls.FISHERIES + cls.SAFETY + cls.ROUTING + cls.RESEARCH

class EvidenceRequirement(BaseModel):
    name: str
    required: bool

class TimeWindow(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class EvidenceContract(BaseModel):
    intent: str = "unknown"
    objective: str
    evidence: List[EvidenceRequirement]
    scientific_analysis: List[str] = []
    time_window: TimeWindow
    location_required: bool = True
    safety_critical: bool = False
    minimum_completeness: float = 1.0
    max_freshness_hours: int = 24

class ValidatedResult(BaseModel):
    is_valid: bool
    confidence: str
    validation_status: str
    assessment_status: str
    certification_status: str
    completeness_score: float
    required_count: int
    met_count: int
    evidence_status: Dict[str, Any]
    scientific_status: Dict[str, Any]
    temporal_validity: bool
    spatial_validity: bool
    causality_status: str
    safety_critical: bool
    freshness_hours: Optional[int] = None
    fallback_used: bool
    dag_data: Dict[str, Any]

class ResultValidator:
    @staticmethod
    def validate(contract: EvidenceContract, dag_result: Dict[str, Any]) -> ValidatedResult:
        evidence_status = {}
        provided_evidence = set()
        max_freshness = 0
        
        # Map DAG data to Ontology keys
        if "agent_results" in dag_result:
            for agent, res in dag_result["agent_results"].items():
                if res.get("status") == "success":
                    data = res.get("data", {})
                    # Fisheries & Ocean
                    if "pfz_candidates" in data or "pfz_score_matrix" in data:
                        provided_evidence.update(["pfz_candidates", "pfz_coordinates", "distance_from_reference", "fishing_opportunity"])
                    if "wave_height" in data or "base_wave_height" in data:
                        provided_evidence.update(["wave_height", "wave_period", "swell", "current_conditions"])
                    if "chlorophyll" in data:
                        provided_evidence.update(["chlorophyll"])
                    if "sst" in data:
                        provided_evidence.update(["sst"])
                    if "sst_series" in data:
                        provided_evidence.update(["sst_series", "chlorophyll_series", "productivity", "fishing_effort"])
                        
                    # Weather
                    if "max_wind_speed" in data:
                        provided_evidence.update(["wind", "forecast_window"])
                    if "hazards" in data:
                        provided_evidence.update(["marine_warnings", "marine_severity"])
                        
                    # Geofencing
                    if "is_inside_eez" in data or "geofence_status" in data:
                        provided_evidence.update(["geofence_status", "restricted_zone_status"])
                    if "route_path" in data:
                        provided_evidence.update(["route_path", "travel_time"])
                        
                    # Research (Temporal arrays)
                    if "cross_source_fusion" in data:
                        provided_evidence.update(["sst_series", "chlorophyll_series", "correlation", "historical_series"])
                        
                    # Routing
                    if "route_path" in data or "decision" in data:
                        provided_evidence.update(["route_path", "travel_time", "route_start_time", "estimated_arrival_time"])
                        
                    # Data freshnes
                    if "metadata" in data and "freshness_hours" in data["metadata"]:
                        fh = data["metadata"]["freshness_hours"]
                        if fh > max_freshness: max_freshness = fh
        
        required_count = 0
        met_count = 0
        for req in contract.evidence:
            avail = req.name in provided_evidence
            evidence_status[req.name] = {"required": req.required, "available": avail}
            if req.required:
                required_count += 1
                if avail: met_count += 1
                
        completeness = met_count / required_count if required_count > 0 else 1.0
        
        temporal_valid = True 
        spatial_valid = True
        fallback_used = False
        
        if max_freshness > contract.max_freshness_hours:
            temporal_valid = False

        causality_status = "NOT_APPLICABLE"
        if "correlation" in contract.scientific_analysis or "causation" in contract.scientific_analysis or contract.intent == "productivity_decline_analysis":
            causality_status = "NOT_ESTABLISHED"
        
        # Safety & Epistemic Verification
        if "agent_results" in dag_result:
            for agent, res in dag_result["agent_results"].items():
                if res.get("status") == "success":
                    data = res.get("data", {})
                    
                    if causality_status == "NOT_ESTABLISHED" and "epistemic_status" in data:
                        if data["epistemic_status"].get("causality_established") == True:
                            causality_status = "ESTABLISHED"
                            
                    if "model_status" in data and data["model_status"] == "DETERMINISTIC_FALLBACK":
                        fallback_used = True
                        
                    if "status" in data and data["status"] == "UNKNOWN_UNAVAILABLE":
                        spatial_valid = False # Geofence fail-closed
        
        # Certification & Confidence Logic
        is_valid = True
        certification = "VALID"
        confidence = "UNKNOWN"
        
        # 1. VALIDATION: Valid only if evidence is complete AND spatially/temporally sound
        validation_status = "VALID" if (completeness == 1.0 and temporal_valid and spatial_valid) else "INCOMPLETE"
        
        # 2. CERTIFICATION: Can we legally/scientifically certify the output?
        if completeness < contract.minimum_completeness:
            is_valid = False
            certification = "NOT_CERTIFIED"
            
        if contract.safety_critical and not spatial_valid:
            is_valid = False
            certification = "NOT_CERTIFIED"
            
        # 3. ASSESSMENT: Extracted from deterministic scientific engines, NOT derived from completeness
        assessment_status = "UNKNOWN"
        if "agent_results" in dag_result:
            risk_data = dag_result["agent_results"].get("risk", {}).get("data", {})
            weather_data = dag_result["agent_results"].get("weather", {}).get("data", {})
            
            # Simulated read from BSI/Safety engine
            if contract.safety_critical:
                if risk_data.get("severity") in ["HIGH", "EXTREME"] or weather_data.get("has_active_alerts") == True:
                    assessment_status = "UNSAFE"
                elif risk_data or weather_data:
                    assessment_status = "SAFE"
                    
            if contract.intent == "safest_route_fishing_vessel":
                geo_data = dag_result["agent_results"].get("geospatial", {}).get("data", {})
                if "route_path" in geo_data:
                    assessment_status = "ROUTE_COMPUTED"
                    
        if assessment_status == "UNKNOWN" and completeness > 0:
            assessment_status = "COMPUTED"

        # 4. CONFIDENCE: Derived dynamically from evidence quality, freshness, and fallbacks
        conf_score = completeness * 100
        if fallback_used: conf_score -= 20
        if not temporal_valid: conf_score -= 30
        if not spatial_valid: conf_score -= 30
        if max_freshness > 6: conf_score -= 10
        
        if conf_score >= 90: confidence = "HIGH"
        elif conf_score >= 60: confidence = "MEDIUM"
        else: confidence = "LOW"
            
        # Deterministic Confidence Matrix
        if certification == "NOT_CERTIFIED":
            confidence = "LOW"
        elif fallback_used:
            confidence = "MEDIUM"
        elif completeness == 1.0 and spatial_valid:
            confidence = "HIGH"
            
        return ValidatedResult(
            is_valid=is_valid,
            confidence=confidence,
            validation_status=validation_status,
            assessment_status=assessment_status,
            certification_status=certification,
            completeness_score=completeness,
            required_count=required_count,
            met_count=met_count,
            evidence_status=evidence_status,
            scientific_status={"fallback_active": fallback_used},
            temporal_validity=temporal_valid,
            spatial_validity=spatial_valid,
            causality_status=causality_status,
            safety_critical=contract.safety_critical,
            freshness_hours=max_freshness,
            fallback_used=fallback_used,
            dag_data=dag_result
        )
