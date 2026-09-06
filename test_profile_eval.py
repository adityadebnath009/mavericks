import cProfile
from app.api.endpoints.safety import get_safety_assessment

cProfile.run('get_safety_assessment(lat=10.1026, lon=72.4300, beam=3.5, day=1, hour=12)', sort='tottime')
