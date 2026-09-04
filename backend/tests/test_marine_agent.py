import pytest
import asyncio
from app.agents.marine_data_agent import MarineDataDiscoveryAgent

@pytest.mark.asyncio
async def test_agent():
    print("--- Initializing Marine Data Discovery Agent ---")
    agent = MarineDataDiscoveryAgent()

    # Coastal test coordinates (Visakhapatnam coast, Bay of Bengal)
    lat, lon = 17.431, 84.703

    print(f"\n[1/2] Fetching Oceanographic Data for ({lat}, {lon})...")
    try:
        ocean_data = await agent.fetch_oceanographic_data(lat=lat, lon=lon, days=1)
        print(" Oceanographic Data Retrieved Successfully:")
        print(f"  - Forecast Steps: {len(ocean_data.time)} hours")
        print(f"  - Wave Heights (first 3 hrs): {ocean_data.wave_height[:3]} m")
        print(f"  - Current Velocities (first 3 hrs): {ocean_data.ocean_current_velocity[:3]} m/s")
        print(f"  - Wave Direction: {ocean_data.wave_direction[:3]}°")
    except Exception as e:
        print(f"❌ Oceanographic Fetch Failed: {e}")

    print(f"\n[2/2] Fetching Meteorological Data for ({lat}, {lon})...")
    try:
        met_data = await agent.fetch_meteorological_data(lat=lat, lon=lon, days=1)
        print(" Meteorological Data Retrieved Successfully:")
        print(f"  - Forecast Steps: {len(met_data.time)} hours")
        print(f"  - Wind Speeds (10m, first 3 hrs): {met_data.wind_speed_10m[:3]} km/h")
        print(f"  - Wind Gusts (first 3 hrs): {met_data.wind_gusts_10m[:3]} km/h")
        print(f"  - Visibility: {met_data.visibility[:3]} m")
    except Exception as e:
        print(f"❌ Meteorological Fetch Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())