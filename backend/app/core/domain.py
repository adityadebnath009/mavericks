from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class EnvironmentSnapshot:
    timestamp: datetime
    lat: float
    lon: float
    wave_height_m: float
    wave_steepness: float
    directional_spread: float
    wind_speed_kmh: float
    wind_direction_deg: float
    current_speed_ms: float
    current_direction_deg: float
    bsi: int
