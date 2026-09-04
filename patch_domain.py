import re

with open("backend/app/core/domain.py", "r") as f:
    content = f.read()

# Add legacy fields to EnvironmentSnapshot to satisfy old tests
new_env = """class EnvironmentSnapshot(BaseModel):
    current: EnvironmentalConditions
    timeline: TimelineSeries
    provenance: Dict[str, ProvenanceRecord]

    # Legacy fields for backward compatibility with SIH tests
    lat: Optional[float] = None
    lon: Optional[float] = None
    wave_steepness: Optional[float] = None
    bsi: Optional[int] = None
    
    @property
    def wave_height_m(self): return self.current.wave_height_m
    @property
    def wind_speed_kmh(self): return self.current.wind_speed_ms * 3.6 if self.current.wind_speed_ms else 0.0
    @property
    def current_speed_ms(self): return self.current.current_speed_ms
    @property
    def current_direction_deg(self): return self.current.current_direction_deg
    @property
    def wind_direction_deg(self): return self.current.wind_direction_deg
    @property
    def directional_spread(self): return self.current.directional_spread
"""

content = content.replace("class EnvironmentSnapshot(BaseModel):\n    current: EnvironmentalConditions\n    timeline: TimelineSeries\n    provenance: Dict[str, ProvenanceRecord]", new_env)

with open("backend/app/core/domain.py", "w") as f:
    f.write(content)
