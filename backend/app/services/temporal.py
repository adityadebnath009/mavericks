import numpy as np
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.research import ResearchDataCube, DataProvenance

class TemporalAnalysisService:
    """
    Performs temporal statistics (trend, anomaly, seasonality) on normalized ResearchDataCube data.
    """
    
    def analyze_cube(self, cube: ResearchDataCube, variable: str, baseline_start: datetime = None, baseline_end: datetime = None) -> Dict[str, Any]:
        """
        Calculates trend, anomaly, and coverage for a specific variable in the DataCube.
        Returns the metrics and the associated DataProvenance.
        """
        # Filter observations for the specific variable
        obs_list = [obs for obs in cube.observations if obs.variable == variable and obs.value is not None]
        
        if not obs_list:
            return {"error": f"No valid data found for variable: {variable}"}
            
        # 1. Coverage
        expected_points = len([obs for obs in cube.observations if obs.variable == variable])
        valid_points = len(obs_list)
        coverage = round(valid_points / expected_points, 3) if expected_points > 0 else 0.0

        # Sort temporally
        obs_list.sort(key=lambda x: x.timestamp)
        timestamps = [obs.timestamp for obs in obs_list]
        values = [obs.value for obs in obs_list]

        # 2. Anomaly Calculation
        # Simple baseline: if dates provided, average over that period. Else, use the first 50% of data.
        if baseline_start and baseline_end:
            baseline_vals = [obs.value for obs in obs_list if baseline_start <= obs.timestamp <= baseline_end]
        else:
            mid = len(values) // 2
            baseline_vals = values[:mid]
            
        baseline_mean = sum(baseline_vals) / len(baseline_vals) if baseline_vals else sum(values)/len(values)
        current_mean = sum(values[-3:]) / min(3, len(values)) if len(values) >= 3 else values[-1]
        anomaly = round(current_mean - baseline_mean, 4)

        # 3. Trend Calculation (Linear Regression via polyfit)
        # Using ordinal dates for X axis
        x_vals = [t.toordinal() for t in timestamps]
        y_vals = values
        
        slope = 0.0
        if len(x_vals) > 1:
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            # Convert slope from per-day to per-year
            slope = round(slope * 365.25, 4)

        # Create Provenance
        sample_obs = obs_list[0]
        provenance = DataProvenance(
            metric=f"{variable}_analysis",
            value=anomaly,
            unit=sample_obs.unit,
            method="linear_regression_and_mean_anomaly",
            period_start=cube.start_time,
            period_end=cube.end_time,
            input_dataset=sample_obs.dataset,
            data_type=sample_obs.data_type,
            coverage=coverage,
            source=sample_obs.provider,
            limitations=["Correlation does not establish causation.", "Linear trend may mask seasonal variance."]
        )
        
        # Append provenance to the cube (mutates the cube)
        cube.provenance.append(provenance)

        return {
            "variable": variable,
            "baseline_mean": round(baseline_mean, 3),
            "current_mean": round(current_mean, 3),
            "anomaly": anomaly,
            "trend_per_year": slope,
            "coverage": coverage,
            "provenance": provenance.model_dump()
        }
