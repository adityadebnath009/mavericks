with open("backend/app/core/domain.py", "r") as f:
    content = f.read()

old_env = """class EnvironmentalConditions(BaseModel):
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
    directional_spread: Optional[float] = None"""

new_env = """class EnvironmentalConditions(BaseModel):
    timestamp: datetime
    wave_height_m: Optional[float] = None
    wave_period_s: Optional[float] = None
    wave_direction_deg: Optional[float] = None
    wind_wave_height_m: Optional[float] = None
    wind_wave_period_s: Optional[float] = None
    wind_wave_direction_deg: Optional[float] = None
    swell_wave_height_m: Optional[float] = None
    swell_wave_period_s: Optional[float] = None
    swell_wave_direction_deg: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    current_speed_ms: Optional[float] = None
    current_direction_deg: Optional[float] = None
    sst_c: Optional[float] = None
    directional_spread: Optional[float] = None"""

content = content.replace(old_env, new_env)

with open("backend/app/core/domain.py", "w") as f:
    f.write(content)
