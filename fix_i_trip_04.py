import os

f = "backend/tests/test_certification_100.py"
with open(f, 'r') as fh: c = fh.read()

c = c.replace(
    'patch(\'app.api.services.trip_decision.PFZRoutingService.calculate_optimal_route\', return_value=_mock_route(status="REJECTED_NO_SAFE_ROUTE")):',
    'patch(\'app.api.services.trip_decision.PFZRoutingService.calculate_optimal_route\', return_value=None):'
)

with open(f, 'w') as fh: fh.write(c)
