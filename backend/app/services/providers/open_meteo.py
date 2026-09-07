import httpx
from typing import List
from datetime import datetime, timedelta
from app.schemas.research import ResearchObservation, RegionSpec
from app.services.providers.base import BaseProvider

class OpenMeteoProvider(BaseProvider):
    async def fetch_observations(
        self, 
        dataset_id: str, 
        region: RegionSpec, 
        start_time: datetime, 
        end_time: datetime,
        variable: str
    ) -> List[ResearchObservation]:
        
        lat = (region.min_lat + region.max_lat) / 2.0
        lon = (region.min_lon + region.max_lon) / 2.0

        # We use archive API for ERA5 reanalysis
        url = "https://archive-api.open-meteo.com/v1/archive"
        
        # In a real environment, we'd pull true SST. For this, temperature_2m over ocean works as a model proxy.
        om_var = "temperature_2m" if variable == "sst" else variable

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d"),
            "hourly": om_var,
            "timezone": "UTC"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        observations = []
        if "hourly" in data and om_var in data["hourly"]:
            times = data["hourly"]["time"]
            values = data["hourly"][om_var]
            
            # Aggregate hourly to daily
            daily_bins = {}
            for t_str, val in zip(times, values):
                if val is not None:
                    day_str = t_str[:10]
                    if day_str not in daily_bins:
                        daily_bins[day_str] = []
                    daily_bins[day_str].append(val)
                    
            for day_str, vals in daily_bins.items():
                if vals:
                    dt = datetime.strptime(day_str, "%Y-%m-%d")
                    avg_val = sum(vals)/len(vals)
                    obs = ResearchObservation(
                        variable=variable,
                        value=avg_val,
                        unit="degC" if variable == "sst" else "unknown",
                        latitude=lat,
                        longitude=lon,
                        timestamp=dt,
                        provider="open_meteo",
                        dataset=dataset_id,
                        data_type="reanalysis"
                    )
                    observations.append(obs)

        return observations
