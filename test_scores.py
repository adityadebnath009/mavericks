from app.api.services.open_meteo_client import open_meteo_client
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.api.services.marine_forecast import MarineForecastService
import datetime
import sys

target_date = datetime.datetime.now(datetime.timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
lat, lon = 15.0, 70.0 # Arabian Sea
try:
    snap = MarineForecastService.get_environment(lat, lon, target_date)
    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=10.0)
    res = engine.evaluate(snap, vessel)
    print("Severity:", res["severity_score"])
    print("Wave Height:", snap.wave_height_m)
    print("Wind Speed:", snap.wind_speed_ms)
except Exception as e:
    print(e)
