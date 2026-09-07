from typing import List, Optional
from datetime import datetime
from app.schemas.research import DatasetRecord

class DatasetRegistryService:
    """
    Resolves scientific evidence requirements into actual datasets/providers.
    Prevents the LLM from hallucinating endpoints.
    """
    def __init__(self):
        # Hardcoded registry for Phase 1. In production, this could be loaded from a DB or YAML.
        self._registry = [
            DatasetRecord(
                dataset_id="NOAA/CDR/OISST/V2_1",
                variable="sst",
                provider="google_earth_engine",
                data_type="satellite_product",
                temporal_coverage_start=datetime(1981, 9, 1),
                spatial_resolution="0.25deg",
                temporal_resolution="daily",
                latency="14 days",
                supported_operations=["mean", "trend", "anomaly"],
                limitations=["Coarse coastal resolution", "Cloud gaps interpolated"]
            ),
            DatasetRecord(
                dataset_id="NASA/OCEANDATA/MODIS-Aqua/L3SMI",
                variable="chlorophyll",
                provider="google_earth_engine",
                data_type="satellite_product",
                temporal_coverage_start=datetime(2002, 7, 4),
                spatial_resolution="4km",
                temporal_resolution="daily",
                latency="1-2 days",
                supported_operations=["mean", "trend"],
                limitations=["Subject to cloud coverage masking"]
            ),
            DatasetRecord(
                dataset_id="open_meteo_marine_era5",
                variable="sst",
                provider="open_meteo",
                data_type="reanalysis",
                temporal_coverage_start=datetime(1940, 1, 1),
                spatial_resolution="0.5deg",
                temporal_resolution="hourly",
                latency="5 days",
                supported_operations=["mean", "trend", "anomaly"],
                limitations=["Model reanalysis, not direct observation"]
            )
        ]

    def resolve_datasets(self, variable: str, preferred_sources: List[str] = None) -> List[DatasetRecord]:
        """
        Finds datasets matching the variable and preferences.
        """
        matches = [d for d in self._registry if d.variable == variable]
        
        if preferred_sources:
            # Filter by preferred source types (e.g. 'satellite', 'reanalysis')
            # Assuming preferred_sources maps roughly to data_type or provider logic
            # For simplicity, we just check if any preferred keyword is in data_type
            filtered = []
            for d in matches:
                if any(pref.lower() in d.data_type.lower() for pref in preferred_sources):
                    filtered.append(d)
            if filtered:
                return filtered
                
        return matches
