import numpy as np
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime
from app.schemas.research import ResearchObservation, DataProvenance

class CrossSourceAnalysisService:
    """
    Computes discrepancies between two different datasets (e.g. Satellite vs Reanalysis).
    Calculates Bias, MAE, RMSE, and Correlation.
    """
    def _align_temporally(self, obs_a: List[ResearchObservation], obs_b: List[ResearchObservation]) -> Tuple[List[float], List[float]]:
        """
        Temporally aligns two observation sets by exact day.
        Returns a tuple of matched value arrays (A_vals, B_vals).
        """
        dict_a = {obs.timestamp.date(): obs.value for obs in obs_a if obs.value is not None}
        dict_b = {obs.timestamp.date(): obs.value for obs in obs_b if obs.value is not None}
        
        common_dates = sorted(list(set(dict_a.keys()).intersection(set(dict_b.keys()))))
        
        a_vals = [dict_a[d] for d in common_dates]
        b_vals = [dict_b[d] for d in common_dates]
        
        return a_vals, b_vals

    def compare_sources(
        self, 
        primary_obs: List[ResearchObservation], 
        reference_obs: List[ResearchObservation]
    ) -> Dict[str, Any]:
        """
        Compares primary (e.g., Satellite) against reference (e.g., Model).
        """
        if not primary_obs or not reference_obs:
            return {"error": "Insufficient data to compare sources."}
            
        p_vals, r_vals = self._align_temporally(primary_obs, reference_obs)
        
        if len(p_vals) < 2:
            return {"error": "Insufficient overlapping temporal data to compare."}
            
        p_arr = np.array(p_vals)
        r_arr = np.array(r_vals)
        
        # Bias: Mean error
        bias = np.mean(p_arr - r_arr)
        
        # MAE: Mean Absolute Error
        mae = np.mean(np.abs(p_arr - r_arr))
        
        # RMSE: Root Mean Squared Error
        rmse = np.sqrt(np.mean((p_arr - r_arr)**2))
        
        # Correlation (Pearson)
        corr_matrix = np.corrcoef(p_arr, r_arr)
        correlation = corr_matrix[0, 1] if not np.isnan(corr_matrix[0, 1]) else 0.0
        
        # Create DataProvenance for the fusion block
        primary_sample = primary_obs[0]
        ref_sample = reference_obs[0]
        
        provenance = DataProvenance(
            metric="cross_source_agreement",
            value=correlation,
            unit="pearson_r",
            method="temporal_alignment_rmse_bias_corr",
            period_start=min(primary_sample.timestamp, ref_sample.timestamp),
            period_end=max(primary_obs[-1].timestamp, reference_obs[-1].timestamp),
            input_dataset=f"{primary_sample.dataset} vs {ref_sample.dataset}",
            data_type="fusion",
            coverage=len(p_vals) / max(len(primary_obs), len(reference_obs)),
            source="orca_fusion_engine"
        )
        
        # Interpretation logic for the LLM
        if correlation > 0.8:
            interp = f"Strong temporal agreement (r={correlation:.2f}) with a {bias:+.2f} bias."
        elif correlation > 0.5:
            interp = f"Moderate temporal agreement (r={correlation:.2f}) with a {bias:+.2f} bias."
        else:
            interp = f"Weak or negligible agreement (r={correlation:.2f}), suggesting source divergence."

        return {
            "bias": round(float(bias), 3),
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "correlation": round(float(correlation), 3),
            "interpretation": interp,
            "provenance": provenance.model_dump()
        }
