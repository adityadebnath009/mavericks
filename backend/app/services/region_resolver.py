import logging
from typing import Dict, List, Tuple
import numpy as np

logger = logging.getLogger("region_resolver")

class RegionResolver:
    """
    Resolves geographic regions into an array of sampling coordinates.
    """
    # V1 Predefined Registry
    REGIONS = {
        "bay of bengal": {
            "lat_min": 10.0,
            "lat_max": 20.0,
            "lon_min": 80.0,
            "lon_max": 90.0
        },
        "arabian sea": {
            "lat_min": 10.0,
            "lat_max": 22.0,
            "lon_min": 60.0,
            "lon_max": 75.0
        },
        "chennai": {
            "lat_min": 12.9,
            "lat_max": 13.2,
            "lon_min": 80.2,
            "lon_max": 80.5
        }
    }

    def resolve(self, query: str, default_lat: float, default_lon: float, grid_spacing: float = 5.0) -> Tuple[List[float], List[float]]:
        """
        Parses the query for known regions and returns a grid of lat/lons.
        If no region is found, returns the default single point.
        Use a coarse grid_spacing (e.g., 5.0 deg) to keep coordinate lists small for Open-Meteo limitations.
        """
        if not query:
            return [default_lat], [default_lon]
            
        lower_query = query.lower()
        matched_region = None
        
        for region_name, bounds in self.REGIONS.items():
            if region_name in lower_query:
                matched_region = bounds
                break
                
        if not matched_region:
            return [default_lat], [default_lon]
            
        # Generate grid
        lats = []
        lons = []
        
        # Open-Meteo allows max ~100 locations per request, but historical hourly data is massive.
        # Limit grid strictly.
        lat_points = np.arange(matched_region["lat_min"], matched_region["lat_max"] + grid_spacing, grid_spacing)
        lon_points = np.arange(matched_region["lon_min"], matched_region["lon_max"] + grid_spacing, grid_spacing)
        
        for lat in lat_points:
            for lon in lon_points:
                lats.append(round(float(lat), 3))
                lons.append(round(float(lon), 3))
                
        # Hard limit to 4 coordinates to prevent 400 Bad Request on massive historical hourly arrays
        lats = lats[:4]
        lons = lons[:4]
        
        logger.info(f"Resolved region '{region_name}' to {len(lats)} sample coordinates.")
        return lats, lons
