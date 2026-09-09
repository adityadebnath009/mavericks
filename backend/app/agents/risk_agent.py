import time
import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentSnapshot
from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../ml/models/sih_orca_risk_classifier.joblib")

class RiskAnalysisAgent(AbstractAgent):
    """Fuses ML XGBoost classifier with Deterministic safety logic."""
    def __init__(self):
        super().__init__()
        self.ml_package = None
        if os.path.exists(MODEL_PATH):
            try:
                self.ml_package = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[RiskAgent] Failed to load ML model: {e}")

    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="risk",
            dependencies=["weather", "ocean", "geospatial"],
            mode_support=["fisheries", "routing"]
        )

    def _predict_ml_risk(self, snapshot: EnvironmentSnapshot, weather_res: dict, ocean_res: dict) -> Dict[str, Any]:
        """Runs the XGBoost model."""
        if not self.ml_package:
            return {"error": "ML model not loaded", "ml_risk_score": 0, "ml_risk_class": "LOW", "model_status": "DETERMINISTIC_FALLBACK"}
            
        try:
            features = self.ml_package["features"]
            model = self.ml_package["model"]
            
            # Map snapshot data to ML feature dict
            row = {f: 0.0 for f in features} # Default all to 0
            
            row["wind_speed_kts"] = weather_res.get("data", {}).get("max_wind_speed", 10.0) / 1.852
            row["wind_gust_kts"] = weather_res.get("data", {}).get("gust_speed", 15.0) / 1.852
            row["wave_height_m"] = ocean_res.get("data", {}).get("base_wave_height", 1.0)
            row["wave_period_s"] = 8.0 # Default
            row["swell_height_m"] = row["wave_height_m"] * 0.5
            
            df = pd.DataFrame([row])
            
            # Base Predict
            pred_class = int(model.predict(df)[0])
            
            # Optional N8 severity refinement
            severity_model = self.ml_package.get("severity_model")
            if pred_class == 2 and severity_model:
                try:
                    method = self.ml_package.get("severity_method")
                    thresh = self.ml_package.get("severity_threshold", 0.5)
                    alpha = self.ml_package.get("severity_alpha", 0.5)
                    
                    base_proba = model.predict_proba(df)
                    pair = base_proba[:, 2] + base_proba[:, 3] + 1e-9
                    base_rel = base_proba[:, 3] / pair
                    
                    if method == "specialist_blend":
                        spec_p = severity_model.predict_proba(df)[:, 1]
                        score = alpha * spec_p + (1.0 - alpha) * base_rel
                    else:
                        score = base_rel
                        
                    if score[0] >= thresh:
                        pred_class = 3
                except Exception:
                    pass
            
            class_map = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "EXTREME"}
            return {
                "ml_risk_score": pred_class,
                "ml_risk_class": class_map.get(pred_class, "UNKNOWN"),
                "status": "success",
                "model_status": "ML_ACTIVE",
                "model_name": self.ml_package.get("model_name", "unknown"),
                "model_version": self.ml_package.get("model_version", "unknown"),
                "framework": self.ml_package.get("framework", "XGBoost"),
                "numpy_version": self.ml_package.get("numpy_version", "unknown"),
                "xgboost_version": self.ml_package.get("xgboost_version", "unknown")
            }
        except Exception as e:
            return {"error": str(e), "ml_risk_score": 0, "ml_risk_class": "LOW", "model_status": "DETERMINISTIC_FALLBACK"}

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        
        weather_res = context.prior_results.get("weather", {})
        ocean_res = context.prior_results.get("ocean", {})
        
        try:
            snapshot = EnvironmentSnapshot(
                wave_height_m=ocean_res.get("data", {}).get("base_wave_height", 1.0),
                wind_speed_kmh=weather_res.get("data", {}).get("max_wind_speed", 10.0),
            )
            
            vessel = VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=8.0)
            
            # 1. Deterministic Engine (BSI)
            engine = OrcaBsiEngine()
            bsi_report = engine.evaluate(snapshot, vessel)
            
            # Map BSI 0-100 severity to risk class
            bsi_score = bsi_report.get("severity_score", 0)
            if bsi_score >= 85: det_class = 3
            elif bsi_score >= 60: det_class = 2
            elif bsi_score >= 35: det_class = 1
            else: det_class = 0
            
            # 2. ML Prediction
            ml_report = self._predict_ml_risk(snapshot, weather_res, ocean_res)
            ml_class = ml_report.get("ml_risk_score", 0)
            
            # 3. Apply Deterministic Floor Failsafe Rule
            # "ML risk output must be capped by deterministic safety floors"
            final_class = max(det_class, ml_class)
            
            class_map = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "EXTREME"}
            final_risk = class_map.get(final_class, "UNKNOWN")
            
            bsi_report["ml_assessment"] = ml_report
            bsi_report["deterministic_class"] = class_map.get(det_class, "LOW")
            bsi_report["final_fused_risk"] = final_risk
            bsi_report["isSafetyFloorTriggered"] = det_class > ml_class
            
            latency = (time.perf_counter() - start_time) * 1000
            
            return AgentResult(
                agent_name=self.spec.name,
                status="success",
                data=bsi_report,
                latency_ms=round(latency, 2),
                sources=["orca_bsi_engine", "xgboost_ml_model"]
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=[str(e)]
            )
