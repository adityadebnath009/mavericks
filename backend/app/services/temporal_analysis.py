import numpy as np
import math
from typing import List, Dict, Any, Optional
from datetime import datetime

class TemporalAnalysisService:
    """
    Performs temporal statistics (trend, anomaly, seasonality) on normalized time-series data.
    """
    def aggregate_monthly(self, timestamps: List[str], values: List[float]) -> Dict[str, float]:
        """Returns monthly averages mapping 'YYYY-MM' -> avg_value."""
        if not values or not timestamps:
            return {}
            
        monthly_bins = {}
        for t, v in zip(timestamps, values):
            if v is None or math.isnan(v):
                continue
            month_key = t[:7]  # YYYY-MM
            if month_key not in monthly_bins:
                monthly_bins[month_key] = []
            monthly_bins[month_key].append(v)
            
        return {k: round(sum(vals)/len(vals), 3) for k, vals in monthly_bins.items()}

    def aggregate_annual(self, timestamps: List[str], values: List[float]) -> Dict[str, float]:
        """Returns annual averages mapping 'YYYY' -> avg_value."""
        if not values or not timestamps:
            return {}
            
        annual_bins = {}
        for t, v in zip(timestamps, values):
            if v is None or math.isnan(v):
                continue
            year_key = t[:4]  # YYYY
            if year_key not in annual_bins:
                annual_bins[year_key] = []
            annual_bins[year_key].append(v)
            
        return {k: round(sum(vals)/len(vals), 3) for k, vals in annual_bins.items()}

    def calculate_trend(self, timestamps: List[str], values: List[float]) -> Optional[Dict[str, Any]]:
        """
        Calculates a simple linear trend per year using least squares over the annual aggregated data.
        Returns None if there is insufficient valid data (e.g., if the model returns nulls).
        """
        annual_data = self.aggregate_annual(timestamps, values)
        if not annual_data or len(annual_data) < 2:
            return None
            
        years = sorted(list(annual_data.keys()))
        y_vals = [annual_data[y] for y in years]
        x_vals = [int(y) for y in years]
        
        # Fit polynomial degree 1
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        
        return {
            "trend_per_year": round(slope, 4),
            "start_mean": y_vals[0],
            "end_mean": y_vals[-1]
        }
