import time
import numpy as np
from typing import Dict, Tuple, List, Any

from app.agents.base import AbstractAgent, AgentSpec
from app.agents.context import AgentContext
from app.agents.result import AgentResult
from app.agents.marine_data_agent import MarineDataDiscoveryAgent

class OceanAnalyticsAgent(AbstractAgent):
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

    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="ocean",
            dependencies=[],
            mode_support=["fisheries", "research", "routing"]
        )

    async def analyze(self, context: AgentContext) -> AgentResult:
        start_time = time.perf_counter()
        
        # Phase T7: Handle Historical Mode
        if context.temporal.mode == "historical":
            from app.services.region_resolver import RegionResolver
            from app.services.temporal_analysis import TemporalAnalysisService
            from app.api.services.open_meteo_client import open_meteo_client
            
            resolver = RegionResolver()
            lats, lons = resolver.resolve(context.query, context.latitude, context.longitude)
            
            try:
                # Fetch multi-coordinate historical data
                raw_data = open_meteo_client.fetch_marine_data(lats, lons, context.temporal)
                
                # The data structure might be an array if multiple coordinates, or a single dict
                if isinstance(raw_data, list):
                    # Average across the grid for each timestamp
                    num_locations = len(raw_data)
                    timestamps = raw_data[0]["hourly"]["time"]
                    
                    sst_values = []
                    current_values = []
                    wave_values = []
                    
                    for i in range(len(timestamps)):
                        # Spatial mean for SST
                        sst_sum = 0.0
                        sst_count = 0
                        for loc_data in raw_data:
                            val = loc_data["hourly"].get("sea_surface_temperature", [])
                            if i < len(val) and val[i] is not None:
                                sst_sum += val[i]
                                sst_count += 1
                        sst_values.append(sst_sum / sst_count if sst_count > 0 else None)
                        
                        # Spatial mean for Current
                        curr_sum = 0.0
                        curr_count = 0
                        for loc_data in raw_data:
                            val = loc_data["hourly"].get("ocean_current_velocity", [])
                            if i < len(val) and val[i] is not None:
                                curr_sum += val[i]
                                curr_count += 1
                        current_values.append(curr_sum / curr_count if curr_count > 0 else None)

                        # Spatial mean for Wave Height
                        wave_sum = 0.0
                        wave_count = 0
                        for loc_data in raw_data:
                            val = loc_data["hourly"].get("wave_height", [])
                            if i < len(val) and val[i] is not None:
                                wave_sum += val[i]
                                wave_count += 1
                        wave_values.append(wave_sum / wave_count if wave_count > 0 else None)
                else:
                    timestamps = raw_data.get("hourly", {}).get("time", [])
                    sst_values = raw_data.get("hourly", {}).get("sea_surface_temperature", [])
                    current_values = raw_data.get("hourly", {}).get("ocean_current_velocity", [])
                    wave_values = raw_data.get("hourly", {}).get("wave_height", [])

                analysis_service = TemporalAnalysisService()
                
                # Process the trends
                sst_trend = analysis_service.calculate_trend(timestamps, sst_values)
                wave_trend = analysis_service.calculate_trend(timestamps, wave_values)
                
                statistics = {}
                if sst_trend is None:
                    statistics["sea_surface_temperature"] = {"error": "Insufficient valid data returned by the requested model."}
                else:
                    statistics["sea_surface_temperature"] = {
                        "trend_per_year": sst_trend["trend_per_year"],
                        "unit": "°C/year",
                        "start_mean": sst_trend["start_mean"],
                        "end_mean": sst_trend["end_mean"]
                    }

                if wave_trend is None:
                    statistics["wave_height"] = {"error": "Insufficient valid data returned by the requested model."}
                else:
                    statistics["wave_height"] = {
                        "trend_per_year": wave_trend["trend_per_year"],
                        "unit": "m/year",
                        "start_mean": wave_trend["start_mean"],
                        "end_mean": wave_trend["end_mean"]
                    }
                
                latency = (time.perf_counter() - start_time) * 1000
                
                return AgentResult(
                    agent_name=self.spec.name,
                    status="success",
                    data={
                        "analysis": {
                            "variable": "sea_surface_temperature",
                            "period": {
                                "start": str(context.temporal.start_date),
                                "end": str(context.temporal.end_date)
                            },
                            "resolution": context.temporal.resolution,
                            "aggregation": "regional_mean"
                        },
                        "statistics": statistics,
                        "provenance": {
                            "provider": "Open-Meteo",
                            "dataset": "ERA5-Ocean",
                            "data_type": "reanalysis",
                            "spatial_resolution": "0.5°",
                            "temporal_resolution": "hourly"
                        }
                    },
                    latency_ms=round(latency, 2),
                    sources=["Open-Meteo ERA5-Ocean Reanalysis"]
                )
            except Exception as e:
                return AgentResult(
                    agent_name=self.spec.name,
                    status="failed",
                    data={},
                    errors=[str(e)]
                )
        
        # Operational Mode Fallback (Original Logic)
        lat = context.latitude
        lon = context.longitude
        if lat is None or lon is None:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=["Latitude and longitude are required in context."]
            )
            
        try:
            discovery = MarineDataDiscoveryAgent()
            ocean_data = await discovery.fetch_oceanographic_data(lat, lon, days=1)
            
            # Extract point data to synthesize spatial grid
            base_sst = ocean_data.sea_surface_temperature[0] if ocean_data.sea_surface_temperature else 28.0
            base_wave = ocean_data.wave_height[0] if ocean_data.wave_height else 1.0
            
            # Synthesize grid
            chl_grid, sst_grid, wave_grid = self.synthesize_spatial_area(base_sst, base_wave)
            
            time_factor = 1.0
            pfz_score, coincidence, hsi = self.score_fishing_grounds(
                chlorophyll_grid=chl_grid,
                sst_grid=sst_grid,
                wave_height_grid=wave_grid,
                time_factor=time_factor
            )
            
            latency = (time.perf_counter() - start_time) * 1000
            
            data = {
                "base_sst": base_sst,
                "base_wave_height": base_wave,
                "pfz_score_matrix": pfz_score.tolist(),
                "coincidence_matrix": coincidence.tolist(),
                "hsi_maps": {k: v.tolist() for k, v in hsi.items()},
                # Legacy compatibility fields for the frontend API response
                "max_pfz_probability": round(float(np.max(pfz_score)), 2),
                "coincidence_edge_detected": bool(np.max(coincidence) > 0.0),
                "highly_suitable_species": [
                    species for species, grid in hsi.items() if np.max(grid) > 0.8
                ]
            }
            
            return AgentResult(
                agent_name=self.spec.name,
                status="success",
                data=data,
                latency_ms=round(latency, 2),
                sources=["open-meteo", "synthetic-spatial-model"]
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.spec.name,
                status="failed",
                data={},
                errors=[str(e)]
            )

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
        x = np.linspace(-1, 1, grid_size)
        y = np.linspace(-1, 1, grid_size)
        xx, yy = np.meshgrid(x, y)
        sst_grid = base_sst + (xx * 1.2) + np.sin(yy * 2.0) * 0.4
        chl_grid = 0.3 + 1.5 * np.exp(-((xx - 0.2)**2 + (yy - 0.1)**2) / 0.4)
        wave_grid = np.clip(base_wave + (yy * 0.2), 0.1, 10.0)
        return chl_grid, sst_grid, wave_grid

    def score_fishing_grounds(self, chlorophyll_grid, sst_grid, wave_height_grid, time_factor):
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