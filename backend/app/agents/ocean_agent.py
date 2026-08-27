import numpy as np
from typing import Dict, Tuple

class OceanAnalyticsAgent:
    """
    Identifies Potential Fishing Zones (PFZs) and species-specific Habitat Suitability Indices (HSI)
    by calculating thermal-chlorophyll coincidence edges across environmental arrays.
    """
    
    def __init__(self):
        # Base PFZ weights documented in the ORCA architecture
        self.weights = {
            'chlorophyll': 0.34,
            'sst': 0.20,
            'thermal_front': 0.16,
            'sea_state': 0.18,
            'time_of_day': 0.12
        }

        # Species-specific optimal SST ranges for HSI scoring (Celsius)
        self.hsi_profiles = {
            'Yellowfin Tuna': {'sst_min': 26.0, 'sst_max': 29.0},
            'Indian Mackerel': {'sst_min': 27.0, 'sst_max': 28.5},
            'Oil Sardine': {'sst_min': 26.5, 'sst_max': 28.0},
            'Silver Pomfret': {'sst_min': 25.0, 'sst_max': 27.5}
        }

    def _normalize(self, array: np.ndarray, invert: bool = False) -> np.ndarray:
        """Normalizes a numpy array to a 0.0 - 1.0 scale."""
        arr_min, arr_max = np.min(array), np.max(array)
        if arr_max == arr_min:
            return np.zeros_like(array)
        
        normalized = (array - arr_min) / (arr_max - arr_min)
        return 1.0 - normalized if invert else normalized

    def calculate_spatial_gradients(self, grid: np.ndarray) -> np.ndarray:
        """Calculates spatial gradient magnitudes |∇| for a given 2D array."""
        dy, dx = np.gradient(grid)
        return np.sqrt(dx**2 + dy**2)

    def calculate_coincidence_edges(self, sst_grid: np.ndarray, chl_grid: np.ndarray) -> np.ndarray:
        """
        Calculates thermal-chlorophyll coincidence edges (3.5x - 4.5x catch enhancement).
        Multiplies the normalized gradients of SST and Chlorophyll-a.
        """
        grad_sst = self._normalize(self.calculate_spatial_gradients(sst_grid))
        grad_chl = self._normalize(self.calculate_spatial_gradients(chl_grid))
        
        # Coincidence edge is strong only where BOTH gradients are high
        return grad_sst * grad_chl

    def calculate_hsi(self, sst_grid: np.ndarray, species: str) -> np.ndarray:
        """Calculates a gaussian Habitat Suitability Index (0.0 to 1.0) based on SST."""
        if species not in self.hsi_profiles:
            return np.zeros_like(sst_grid)
            
        profile = self.hsi_profiles[species]
        optimal_center = (profile['sst_max'] + profile['sst_min']) / 2.0
        range_width = (profile['sst_max'] - profile['sst_min']) / 2.0
        
        # Score drops off as temperature deviates from the optimal center
        hsi_grid = np.exp(-0.5 * ((sst_grid - optimal_center) / range_width)**2)
        return self._normalize(hsi_grid)

    def score_fishing_grounds(self, 
                              chlorophyll_grid: np.ndarray, 
                              sst_grid: np.ndarray, 
                              wave_height_grid: np.ndarray,
                              time_factor: float) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """
        Combines variables into a final 'chance of fish' probability map, 
        returns the coincidence edge map, and calculates HSI for targeted species.
        """
        # 1. Gradients and Coincidence
        front_grid = self.calculate_spatial_gradients(sst_grid)
        coincidence_grid = self.calculate_coincidence_edges(sst_grid, chlorophyll_grid)
        
        # 2. Normalize base factors
        norm_chloro = self._normalize(chlorophyll_grid)
        norm_sst = self._normalize(sst_grid) 
        norm_front = self._normalize(front_grid)
        
        # Sea state is inverted: higher waves = worse fishing chance
        norm_sea_state = self._normalize(wave_height_grid, invert=True)
        
        # 3. Apply baseline weights
        pfz_score = (
            (norm_chloro * self.weights['chlorophyll']) +
            (norm_sst * self.weights['sst']) +
            (norm_front * self.weights['thermal_front']) +
            (norm_sea_state * self.weights['sea_state']) +
            (time_factor * self.weights['time_of_day'])
        )
        
        # 4. Enhance score using thermal-chlorophyll coincidence edges
        enhanced_pfz_score = self._normalize(pfz_score + (coincidence_grid * 0.5))

        # 5. Generate Species-Specific HSI Maps
        hsi_maps = {
            species: self.calculate_hsi(sst_grid, species)
            for species in self.hsi_profiles.keys()
        }
        
        return enhanced_pfz_score, coincidence_grid, hsi_maps