from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from app.schemas.research import ResearchObservation, RegionSpec

class BaseProvider(ABC):
    """
    Abstract base class for all data providers (GEE, Open-Meteo, INCOIS, GFW).
    Enforces that providers return canonical ResearchObservations.
    """
    
    @abstractmethod
    async def fetch_observations(
        self, 
        dataset_id: str, 
        region: RegionSpec, 
        start_time: datetime, 
        end_time: datetime,
        variable: str
    ) -> List[ResearchObservation]:
        """
        Fetches data from the provider and normalizes it into ResearchObservations.
        """
        pass
