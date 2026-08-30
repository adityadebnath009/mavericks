import numpy as np
from typing import Dict, Tuple, List

class OceanAnalyticsAgent:
    def __init__(self):
        self.weights = {
            'chlorophyll': 0.34,
            'sst': 0.20,
            'thermal_front': 0.16,
            'sea_state': 0.18,
            'time_of_day': 0.12
        }
        self.hsi_profiles = {
            'Yellowfin Tuna': {'sst_min': 26.0, 'sst_max': 29.0},
            'Indian Mackerel': {'sst_min': 27.0, 'sst_max': 28.5},
            'Oil Sardine': {'sst_min': 26.5, 'sst_max': 28.0},
            'Silver Pomfret': {'sst_min': 25.0, 'sst_max': 27.5}
        }

    def _normalize(self, array: np.ndarray, invert: bool = False) -> np.ndarray:
        arr_min, arr_max = np.min(array), np.max(array)
        if np.isclose(arr_max, arr_min):
            return np.ones_like(array) * 0.5 if invert else np.zeros_like(array)
        normalized = (array - arr_min) / (arr_max - arr_min)
        return 1.0 - normalized if invert else normalized

    def calculate_spatial_gradients(self, grid: np.ndarray) -> np.ndarray:
        dy, dx = np.gradient(grid)
        return np.sqrt(dx**2 + dy**2)

    def calculate_coincidence_edges(self, sst_grid: np.ndarray, chl_grid: np.ndarray) -> np.ndarray:
        grad_sst = self._normalize(self.calculate_spatial_gradients(sst_grid))
        grad_chl = self._normalize(self.calculate_spatial_gradients(chl_grid))
        return grad_sst * grad_chl

    def calculate_hsi(self, sst_grid: np.ndarray, species: str) -> np.ndarray:
        if species not in self.hsi_profiles:
            return np.zeros_like(sst_grid)
        profile = self.hsi_profiles[species]
        optimal_center = (profile['sst_max'] + profile['sst_min']) / 2.0
        range_width = (profile['sst_max'] - profile['sst_min']) / 2.0
        hsi_grid = np.exp(-0.5 * ((sst_grid - optimal_center) / range_width)**2)
        return self._normalize(hsi_grid)

    def synthesize_spatial_area(self, base_sst: float, base_wave: float, grid_size: int = 10) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generates realistic spatial variance around point data for gradient analysis."""
        x = np.linspace(-1, 1, grid_size)
        y = np.linspace(-1, 1, grid_size)
        xx, yy = np.meshgrid(x, y)
        
        # Add thermal gradient across the grid (+- 1.5°C)
        sst_grid = base_sst + (xx * 1.2) + np.sin(yy * 2.0) * 0.4
        
        # Chlorophyll concentration blooms near upwelling edges
        chl_grid = 0.3 + 1.5 * np.exp(-((xx - 0.2)**2 + (yy - 0.1)**2) / 0.4)
        
        # Wave height slight spatial variation
        wave_grid = np.clip(base_wave + (yy * 0.2), 0.1, 10.0)
        
        return chl_grid, sst_grid, wave_grid

    def score_fishing_grounds(self,
                              chlorophyll_grid: np.ndarray,
                              sst_grid: np.ndarray,
                              wave_height_grid: np.ndarray,
                              time_factor: float) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        front_grid = self.calculate_spatial_gradients(sst_grid)
        coincidence_grid = self.calculate_coincidence_edges(sst_grid, chlorophyll_grid)

        norm_chloro = self._normalize(chlorophyll_grid)
        norm_sst = self._normalize(sst_grid)
        norm_front = self._normalize(front_grid)
        norm_sea_state = self._normalize(wave_height_grid, invert=True)

        pfz_score = (
            (norm_chloro * self.weights['chlorophyll']) +
            (norm_sst * self.weights['sst']) +
            (norm_front * self.weights['thermal_front']) +
            (norm_sea_state * self.weights['sea_state']) +
            (time_factor * self.weights['time_of_day'])
        )

        enhanced_pfz_score = self._normalize(pfz_score + (coincidence_grid * 0.5))
        hsi_maps = {
            species: self.calculate_hsi(sst_grid, species)
            for species in self.hsi_profiles.keys()
        }
        return enhanced_pfz_score, coincidence_grid, hsi_maps