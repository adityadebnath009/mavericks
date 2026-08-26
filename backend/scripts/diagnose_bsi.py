import sys
import os
import math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.api.services.incois_resolver import IncoisDatasetResolver
from app.api.services.bsi_calculator import BSICalculator

def diagnose():
    test_points = [
        (15.0, 73.0, "Goa Coast"),
        (10.0, 65.0, "Arabian Sea Offshore"),
        (12.0, 85.0, "Bay of Bengal Offshore"),
        (8.0, 72.0, "Lakshadweep Offshore"),
        (20.0, 68.0, "Gujarat Offshore")
    ]
    
    for lat, lon, label in test_points:
        for day in [1, 2, 3]:
            try:
                ww3, curr = IncoisDatasetResolver.resolve_latest_forecast(lat, lon, day)
                found_non_zero = False
                for k, step in enumerate(ww3):
                    hs = step["hs"]
                    stp = step["stp"]
                    spr = step["spr"]
                    hsea_initial = step["hsea_initial"]
                    hsea_final = step["hsea_final"]
                    
                    I_steepness = BSICalculator.calculate_steepness_index(stp, hs)
                    I_crossing = BSICalculator.calculate_crossing_sea_index(hs, spr)
                    Z_6h = BSICalculator.calculate_rapid_dev_index(hsea_initial, hsea_final)
                    
                    bsi = BSICalculator.calculate_bsi(stp, hs, spr, hsea_initial, hsea_final)
                    
                    if bsi > 0:
                        found_non_zero = True
                        print(f"[{label} - Day {day} - Step {k}]: BSI={bsi}!")
                        print(f"  Hs={hs:.3f}, Stp={stp:.5f}, Spr={spr:.3f}")
                        print(f"  I_steepness={I_steepness:.4f} (>=0.8? {'YES' if I_steepness >= 0.8 else 'NO'})")
                        print(f"  I_crossing={I_crossing:.4f} (>=0.65? {'YES' if I_crossing >= 0.65 else 'NO'})")
                        print(f"  Z_6h={Z_6h:.4f} (>=0.2? {'YES' if Z_6h >= 0.2 else 'NO'})")
            except Exception as e:
                print(f"  Error querying {label} on Day {day}: {e}")

if __name__ == "__main__":
    diagnose()
