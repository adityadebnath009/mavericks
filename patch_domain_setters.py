import re

with open("backend/app/core/domain.py", "r") as f:
    content = f.read()

setters = """
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
"""

# Append the setters to the end of the EnvironmentSnapshot class
content = content + setters

with open("backend/app/core/domain.py", "w") as f:
    f.write(content)
