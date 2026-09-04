import asyncio
import time
import datetime
from app.api.services.marine_forecast import MarineForecastService

def run():
    lat = 15.0
    lon = 72.0
    ts = datetime.datetime.now(datetime.timezone.utc)
    
    t0 = time.time()
    env = MarineForecastService.get_environment(lat, lon, ts)
    t1 = time.time()
    
    print(f"First fetch: {(t1 - t0)*1000:.2f} ms")
    
    # Test cache
    t2 = time.time()
    env = MarineForecastService.get_environment(lat, lon, ts)
    t3 = time.time()
    
    print(f"Cached fetch: {(t3 - t2)*1000:.2f} ms")
    print("EnvironmentSnapshot:")
    print("Wave Height:", env.current.wave_height_m)
    print("Wind Speed:", env.current.wind_speed_ms)
    print("SST:", env.current.sst_c)
    print("Provenance SST:", env.provenance["sst_c"].source)

if __name__ == "__main__":
    run()
