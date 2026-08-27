import numpy as np
from typing import Dict

class OceanAnalyticsAgent:
    """
    Identifies Potential Fishing Zones (PFZs) by mathematically correlating 
    SST gradients, Chlorophyll-a concentrations, and sea-state arrays.
    """
    
    def __init__(self):
        # ORCA documented fishing model weights
        self.weights = {
            'chlorophyll': 0.34,
            'sst': 0.20,
            'thermal_front': 0.16,
            'sea_state': 0.18,
            'time_of_day': 0.12
        }

    def _normalize(self, array: np.ndarray, invert: bool = False) -> np.ndarray:
        """Normalizes an array to a 0-1 scale. Inverts if lower is better (e.g., rough sea state)."""
        arr_min, arr_max = np.min(array), np.max(array)
        if arr_max == arr_min:
            return np.zeros_like(array)
        
        normalized = (array - arr_min) / (arr_max - arr_min)
        return 1.0 - normalized if invert else normalized

    def calculate_thermal_fronts(self, sst_grid: np.ndarray) -> np.ndarray:
        """Calculates spatial SST gradients to find sharp temperature changes."""
        # Using numpy gradient to find directional changes, then calculating magnitude
        dy, dx = np.gradient(sst_grid)
        front_strength = np.sqrt(dx**2 + dy**2)
        return front_strength

    def score_fishing_grounds(self, 
                              chlorophyll_grid: np.ndarray, 
                              sst_grid: np.ndarray, 
                              wave_height_grid: np.ndarray,
                              time_factor: float) -> np.ndarray:
        """
        Combines variables into a final 'chance of fish' probability map.
        Arrays should be 2D numpy grids representing the spatial area.
        """
        # 1. Calculate thermal front strength from SST
        front_grid = self.calculate_thermal_fronts(sst_grid)
        
        # 2. Normalize all factors to 0.0 - 1.0 scales
        norm_chloro = self._normalize(chlorophyll_grid)
        norm_sst = self._normalize(sst_grid) 
        norm_front = self._normalize(front_grid)
        
        # Sea state is inverted: higher waves = worse fishing chance
        norm_sea_state = self._normalize(wave_height_grid, invert=True)
        
        # 3. Apply weights
        pfz_score = (
            (norm_chloro * self.weights['chlorophyll']) +
            (norm_sst * self.weights['sst']) +
            (norm_front * self.weights['thermal_front']) +
            (norm_sea_state * self.weights['sea_state']) +
            (time_factor * self.weights['time_of_day'])
        )
        
        return pfz_score