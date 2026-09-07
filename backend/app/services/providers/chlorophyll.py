import ee
from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio

from app.schemas.research import ResearchObservation, RegionSpec
from app.services.providers.base import BaseProvider

class ChlorophyllProvider(BaseProvider):
    """
    Retrieves Chlorophyll-a data from Google Earth Engine.
    Uses NASA MODIS Aqua L3SMI composite to avoid 5-minute OC4 computation timeouts on live clicks.
    """
    
    def __init__(self):
        # We assume ee.Initialize() is handled centrally, but can re-verify here if needed
        pass

    async def fetch_observations(
        self, 
        dataset_id: str, 
        region: RegionSpec, 
        start_time: datetime, 
        end_time: datetime,
        variable: str = "chlor_a"
    ) -> List[ResearchObservation]:
        
        # We run the GEE network call in a thread pool to avoid blocking FastAPI
        return await asyncio.to_thread(
            self._execute_gee_reduction, 
            dataset_id, region, start_time, end_time, variable
        )
        
    def _execute_gee_reduction(
        self, 
        dataset_id: str, 
        region: RegionSpec, 
        start_time: datetime, 
        end_time: datetime,
        variable: str
    ) -> List[ResearchObservation]:
        
        # NASA/OCEANDATA/MODIS-Aqua/L3SMI is preferred for fast pre-calculated Chl-a
        collection_id = dataset_id if dataset_id else "NASA/OCEANDATA/MODIS-Aqua/L3SMI"
        
        # Create point geometry from RegionSpec (assuming single click query)
        center_lat = (region.min_lat + region.max_lat) / 2
        center_lon = (region.min_lon + region.max_lon) / 2
        point = ee.Geometry.Point([center_lon, center_lat])
        
        # Hackathon fix: Since MODIS L3 has ingestion latency (months), 
        # if the requested date has no data, we fallback to a composite 
        # from the latest available dataset window (e.g. late 2025).
        
        col = ee.ImageCollection(collection_id)\
            .select(variable)\
            .filterBounds(point)\
            .filterDate(
                (end_time - timedelta(days=60)).strftime('%Y-%m-%d'), 
                end_time.strftime('%Y-%m-%d')
            )
            
        # If the temporal filter is empty (due to latency), grab the latest absolute 30 days
        size = col.size().getInfo()
        if size == 0:
            latest_col = ee.ImageCollection(collection_id).select(variable).filterBounds(point).sort('system:time_start', False)
            latest_image = latest_col.first()
            latest_date_str = ee.Date(latest_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
            col = ee.ImageCollection(collection_id)\
                .select(variable)\
                .filterBounds(point)\
                .filterDate(
                    (latest_date - timedelta(days=30)).strftime('%Y-%m-%d'),
                    (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')
                )
                
        # We use a mean composite over time to penetrate cloud masks
        image = col.mean()
        
        # Reduce to a scalar value
        val = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=4000
        ).getInfo()
        
        value = val.get(variable)
        
        
        # Calculate freshness
        actual_date = latest_date if size == 0 else end_time
        now = datetime.utcnow()
        freshness_hours = int((now - actual_date).total_seconds() / 3600)
        
        # Wrap into our canonical ResearchObservation
        obs = ResearchObservation(
            timestamp=end_time, # Tag with requested time
            value=value if value is not None else 0.0,
            unit="mg/m^3",
            metadata={
                "source": "MODIS Aqua", 
                "composite": "30-day",
                "processing": "cached",
                "data_timestamp": actual_date.isoformat() + "Z",
                "freshness_hours": freshness_hours
            }
        )
        
        return [obs]
