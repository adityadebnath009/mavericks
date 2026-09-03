from app.core.domain import EnvironmentSnapshot
import datetime

env = EnvironmentSnapshot(
    wave_height_m=3.0,
    timestamp=datetime.datetime.now()
)
print("wave_height_m:", env.wave_height_m)
print("_legacy_wave_height_m:", env._legacy_wave_height_m)
