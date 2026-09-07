import asyncio
import ee
from typing import List
from datetime import datetime
from app.schemas.research import ResearchObservation, RegionSpec
from app.services.providers.base import BaseProvider
from app.services.providers.registry import DatasetRegistryService

class GEEProvider(BaseProvider):
    """
    Acquires data from Google Earth Engine and formats it into ResearchObservations.
    """
    def __init__(self, registry: DatasetRegistryService):
        self.registry = registry

    async def fetch_observations(
        self, 
        dataset_id: str, 
        region: RegionSpec, 
        start_time: datetime, 
        end_time: datetime,
        variable: str
    ) -> List[ResearchObservation]:
        
        return await asyncio.to_thread(
            self._fetch_timeseries_sync, dataset_id, region, start_time, end_time, variable
        )

    def _fetch_timeseries_sync(
        self, 
        dataset_id: str, 
        region: RegionSpec, 
        start_time: datetime, 
        end_time: datetime,
        variable: str
    ) -> List[ResearchObservation]:
        """
        Synchronous Earth Engine API call to fetch a time-series of spatial means.
        """
        geom = ee.Geometry.Rectangle([
            region.min_lon, region.min_lat,
            region.max_lon, region.max_lat
        ])

        collection = ee.ImageCollection(dataset_id)
        collection = collection.filterDate(
            start_time.strftime('%Y-%m-%d'), 
            end_time.strftime('%Y-%m-%d')
        ).filterBounds(geom)

        # To prevent massive timeouts on daily data over 10 years, we can aggregate by month.
        # But for Phase 2 simplicity, let's just assume we want monthly means for the timeseries.
        
        # Define a function to calculate the mean of the region for a single image
        def get_region_mean(image):
            # Calculate the spatial mean
            stats = image.select(variable).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geom,
                scale=27750,
                maxPixels=1e9
            )
            # Return a feature with the value and the timestamp
            return ee.Feature(None, {
                'value': stats.get(variable),
                'time': image.get('system:time_start')
            })

        # Map the function over the collection
        time_series = collection.map(get_region_mean)
        
        # Execute the graph and pull JSON to Python
        # .getInfo() fetches the list of features
        try:
            results = time_series.getInfo()
        except Exception as e:
            return []

        observations = []
        features = results.get('features', [])
        
        for feat in features:
            props = feat.get('properties', {})
            val = props.get('value')
            time_ms = props.get('time')
            
            if val is not None and time_ms is not None:
                dt = datetime.utcfromtimestamp(time_ms / 1000.0)
                
                obs = ResearchObservation(
                    variable=variable,
                    value=val,
                    unit="degC" if variable == "sst" else "mg/m^3",
                    latitude=(region.min_lat + region.max_lat) / 2.0,
                    longitude=(region.min_lon + region.max_lon) / 2.0,
                    timestamp=dt,
                    provider="google_earth_engine",
                    dataset=dataset_id,
                    data_type="satellite_product"
                )
                observations.append(obs)

        return observations
