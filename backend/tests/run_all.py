import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_bsi_calculator import (
    test_steepness_index,
    test_crossing_sea_index,
    test_rapid_dev_index,
    test_all_bsi_combinations,
    test_bsi_details_decoding,
    test_vessel_beam_safety
)
from tests.test_incois_resolver import (
    test_cache_paths,
    test_remote_resolve
)
from tests.test_incois_geoserver import (
    test_get_capabilities,
    test_get_feature_info,
    test_get_pfz_lines_wfs
)

if __name__ == "__main__":
    print("Running all backend verification tests...")
    try:
        test_steepness_index()
        print("✓ test_steepness_index passed.")
        test_crossing_sea_index()
        print("✓ test_crossing_sea_index passed.")
        test_rapid_dev_index()
        print("✓ test_rapid_dev_index passed.")
        test_all_bsi_combinations()
        print("✓ test_all_bsi_combinations passed.")
        test_bsi_details_decoding()
        print("✓ test_bsi_details_decoding passed.")
        test_vessel_beam_safety()
        print("✓ test_vessel_beam_safety passed.")
        test_cache_paths()
        print("✓ test_cache_paths passed.")
        
        # Runs remote OPeNDAP connection test
        test_remote_resolve()
        print("✓ test_remote_resolve passed.")
        
        # WMS/WFS GeoServer tests
        test_get_capabilities()
        print("✓ test_get_capabilities passed.")
        test_get_feature_info()
        print("✓ test_get_feature_info passed.")
        test_get_pfz_lines_wfs()
        print("✓ test_get_pfz_lines_wfs passed.")
        
        print("\nAll backend tests passed successfully!")
    except AssertionError as e:
        print(f"FAIL: Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error occurred: {e}")
        sys.exit(1)
