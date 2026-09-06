import sys
sys.path.append("backend")
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from tests.test_certification_100 import create_safe_env

env = create_safe_env(hs=0.5)
vessel = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=15.0)
res = OrcaBsiEngine().evaluate(env, vessel)
print("BSI RESULT IS", res)
