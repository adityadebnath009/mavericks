import sys
sys.path.append("backend")
from app.api.endpoints.safety import _compute_grid
try:
    res = _compute_grid(1, 12)
    print(res['features'][0]['properties'])
except Exception as e:
    import traceback
    traceback.print_exc()
