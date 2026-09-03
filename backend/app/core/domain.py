from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EnvironmentalConditions(BaseModel):
    timestamp: datetime
    wave_height_m: Optional[float] = None
    wave_period_s: Optional[float] = None
    wave_direction_deg: Optional[float] = None
    wind_wave_height_m: Optional[float] = None
    wind_wave_period_s: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    current_speed_ms: Optional[float] = None
    current_direction_deg: Optional[float] = None
    sst_c: Optional[float] = None
    directional_spread: Optional[float] = None

class TimelineSeries(BaseModel):
    timestamps: List[datetime] = Field(default_factory=list)
    wave_height_m: List[Optional[float]] = Field(default_factory=list)
    wave_period_s: List[Optional[float]] = Field(default_factory=list)
    wind_speed_ms: List[Optional[float]] = Field(default_factory=list)
    current_speed_ms: List[Optional[float]] = Field(default_factory=list)

class ProvenanceRecord(BaseModel):
    source: str
    fallback: bool = False
    observed_at: datetime
    cached: bool = False
    age_minutes: int = 0

class EnvironmentSnapshot(BaseModel):
    current: Optional[EnvironmentalConditions] = None
    timeline: Optional[TimelineSeries] = None
    provenance: Optional[Dict[str, ProvenanceRecord]] = None

    # Legacy fields for backward compatibility with SIH tests
    lat: Optional[float] = None
    lon: Optional[float] = None
    wave_steepness: Optional[float] = None
    bsi: Optional[int] = None
    
    # Added dynamic shadow field to prevent infinite recursion
    _legacy_wave_height_m: Optional[float] = None
    _legacy_wind_speed_kmh: Optional[float] = None
    _legacy_current_speed_ms: Optional[float] = None
    _legacy_current_direction_deg: Optional[float] = None
    _legacy_wind_direction_deg: Optional[float] = None
    _legacy_directional_spread: Optional[float] = None

    def __init__(self, **data):
        super().__init__(**data)
        # Store legacy direct kwargs for testing
        self._legacy_wave_height_m = data.get('wave_height_m')
        self._legacy_wind_speed_kmh = data.get('wind_speed_kmh')
        self._legacy_current_speed_ms = data.get('current_speed_ms')
        self._legacy_current_direction_deg = data.get('current_direction_deg')
        self._legacy_wind_direction_deg = data.get('wind_direction_deg')
        self._legacy_directional_spread = data.get('directional_spread')

    @property
    def wave_height_m(self): 
        return self.current.wave_height_m if self.current else self._legacy_wave_height_m
    @property
    def wind_speed_kmh(self): 
        return (self.current.wind_speed_ms * 3.6 if self.current.wind_speed_ms else 0.0) if self.current else self._legacy_wind_speed_kmh
    @property
    def current_speed_ms(self): 
        return self.current.current_speed_ms if self.current else self._legacy_current_speed_ms
    @property
    def current_direction_deg(self): 
        return self.current.current_direction_deg if self.current else self._legacy_current_direction_deg
    @property
    def wind_direction_deg(self): 
        return self.current.wind_direction_deg if self.current else self._legacy_wind_direction_deg
    @property
    def directional_spread(self): 
        return self.current.directional_spread if self.current else self._legacy_directional_spread


    @wave_height_m.setter
    def wave_height_m(self, val): 
        if self.current: self.current.wave_height_m = val
        else: self._legacy_wave_height_m = val
        
    @wind_speed_kmh.setter
    def wind_speed_kmh(self, val): 
        if self.current: self.current.wind_speed_ms = val / 3.6
        else: self._legacy_wind_speed_kmh = val
        
    @current_speed_ms.setter
    def current_speed_ms(self, val): 
        if self.current: self.current.current_speed_ms = val
        else: self._legacy_current_speed_ms = val
        
    @current_direction_deg.setter
    def current_direction_deg(self, val): 
        if self.current: self.current.current_direction_deg = val
        else: self._legacy_current_direction_deg = val
        
    @wind_direction_deg.setter
    def wind_direction_deg(self, val): 
        if self.current: self.current.wind_direction_deg = val
        else: self._legacy_wind_direction_deg = val
        
    @directional_spread.setter
    def directional_spread(self, val): 
        if self.current: self.current.directional_spread = val
        else: self._legacy_directional_spread = val
