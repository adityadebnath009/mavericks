import sys
sys.path.append('backend')
from app.api.services.orca_bsi_engine import OrcaBsiEngine

engine = OrcaBsiEngine()

print("=== TEST 2: Boundary Scoring (3. BSI Score Boundary Tests) ===")
test_cases = [0, 20, 21, 50, 51, 75, 76, 100]

for score in test_cases:
    rating = engine.classify_severity(score)
    print(f"Score {score} -> {rating}")
