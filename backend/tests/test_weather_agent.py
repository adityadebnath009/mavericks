import pytest
import asyncio
from datetime import datetime, timedelta
from app.agents.marine_data_agent import MarineDataDiscoveryAgent, MeteorologicalData
from app.agents.weather_agent import WeatherIntelligenceAgent

@pytest.mark.asyncio
async def test_weather_agent():
    print("=== Testing Weather Intelligence Agent ===")
    weather_agent = WeatherIntelligenceAgent()

    # --- Scenario 1: Live API Data ---
    discovery_agent = MarineDataDiscoveryAgent()
    lat, lon = 17.431, 84.703  # Bay of Bengal / Vizag
    print(f"\n[Test 1] Running live weather evaluation for ({lat}, {lon})...")
    
    try:
        live_met = await discovery_agent.fetch_meteorological_data(lat, lon, days=1)
        report = weather_agent.analyze(live_met)
        print(f"Status: OK | Active Alerts: {report.has_active_alerts} | Severity: {report.highest_severity.value}")
        print(f"Summary: {report.plain_language_summary}")
    except Exception as e:
        print(f"Live fetch skipped/failed: {e}")

    # --- Scenario 2: Simulated Severe Cyclonic Squall & Lightning ---
    print("\n[Test 2] Simulating Severe Cyclone & Cloud-to-Sea Lightning...")
    now = datetime.utcnow()
    synthetic_met = MeteorologicalData(
        time=[now + timedelta(hours=i) for i in range(4)],
        wind_speed_10m=[25.0, 48.0, 92.0, 30.0],          # Normal -> Squall -> Severe Cyclone (>=89) -> Normal
        wind_gusts_10m=[35.0, 58.0, 110.0, 42.0],
        precipitation_probability=[10, 40, 85, 20],        # Hour 2 breaches 70% for lightning strike
        weather_code=[1, 95, 99, 2],                      # Code 95 (Thunderstorm), Code 99 (Cloud-to-Sea Lightning)
        visibility=[8000.0, 1200.0, 400.0, 6000.0]        # 400m = Low visibility hazard
    )

    synth_report = weather_agent.analyze(synthetic_met)
    print(f"Status: OK | Severity: {synth_report.highest_severity.value}")
    print(f"Hazards Detected: {synth_report.active_hazards}")
    print(f"Total Alerts Triggered: {len(synth_report.timeline_alerts)}")
    print(f"Summary: {synth_report.plain_language_summary}")

    # Assert upgraded hazard labels
    assert "Cyclone Danger Radius" in synth_report.active_hazards
    assert "Cloud-to-Sea Lightning" in synth_report.active_hazards
    assert "Low Visibility" in synth_report.active_hazards
    assert synth_report.highest_severity.value == "EXTREME"
    print("\n All upgraded threshold assertions passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_weather_agent())