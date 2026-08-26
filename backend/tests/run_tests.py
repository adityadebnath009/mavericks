import sys
from test_bsi_calculator import (
    test_steepness_index,
    test_crossing_sea_index,
    test_rapid_dev_index,
    test_all_bsi_combinations,
    test_bsi_details_decoding,
    test_vessel_beam_safety
)

def run():
    print("Running BSI Calculator Tests...")
    print("--------------------------------")
    try:
        test_steepness_index()
        print("✓ test_steepness_index passed")
        test_crossing_sea_index()
        print("✓ test_crossing_sea_index passed")
        test_rapid_dev_index()
        print("✓ test_rapid_dev_index passed")
        test_all_bsi_combinations()
        print("✓ test_all_bsi_combinations passed")
        test_bsi_details_decoding()
        print("✓ test_bsi_details_decoding passed")
        test_vessel_beam_safety()
        print("✓ test_vessel_beam_safety passed")
        print("--------------------------------")
        print("ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    except AssertionError as e:
        import traceback
        print("Assertion Error encountered during testing!")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print("Unexpected error encountered during testing:")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    run()
