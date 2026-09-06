import time
from app.api.endpoints.safety import get_safety_assessment

t0 = time.time()
try:
    res = get_safety_assessment(lat=10.1026, lon=72.4300, beam=3.5, day=1, hour=12)
    print("Time:", time.time() - t0)
except Exception as e:
    print("Error:", e)
