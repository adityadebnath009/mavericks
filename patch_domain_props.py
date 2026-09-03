import re

with open("backend/app/core/domain.py", "r") as f:
    content = f.read()

# Replace the simple properties with fallback properties
old_props = """    @property
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
    def directional_spread(self): return self.current.directional_spread"""

new_props = """    # Added dynamic shadow field to prevent infinite recursion
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
        return self.current.directional_spread if self.current else self._legacy_directional_spread"""

content = content.replace(old_props, new_props)

with open("backend/app/core/domain.py", "w") as f:
    f.write(content)
