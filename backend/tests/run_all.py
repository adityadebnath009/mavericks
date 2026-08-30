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
from tests.test_pfz_intelligence import (
    test_haversine_distance,
    test_pfz_evaluation,
    test_pfz_invalid_id
)
from tests.test_trip_decision import (
    test_temporal_forecast_resolver_interpolation,
    test_time_dependent_pfz_routing,
    test_pfz_candidate_evaluation_and_ranking,
    test_dynamic_temporal_wave_jump_routing,
    test_routing_with_zero_current,
    test_routing_extreme_wind_rejection,
    test_empty_pfz_advisory_handling
)
from tests.test_pfz_enricher import (
    test_enrich_point_schema,
    test_enrich_point_bounds_validation,
    test_enrich_point_grid_caching,
    test_enrich_pfz_linestring_sampling,
    test_enrich_pfz_multilinestring_sampling,
    test_enrich_pfz_degenerate_geometry,
    test_enrich_pfz_geometry_hash_caching,
    test_catch_score_logic,
    test_enrich_feature_collection,
    test_point_analytics_endpoint,
    test_pfz_lines_endpoint_enrichment,
    test_multi_tier_failsafe_hierarchy,
    test_cache_thread_safety,
    test_empirical_cache_latency_benchmark,
    test_empirical_quantization_accuracy,
    test_geometry_hash_and_epoch_rollover,
    test_zero_static_fish_or_species_names
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
        
        # PFZ Intelligence tests
        test_haversine_distance()
        print("✓ test_haversine_distance passed.")
        test_pfz_evaluation()
        print("✓ test_pfz_evaluation passed.")
        test_pfz_invalid_id()
        print("✓ test_pfz_invalid_id passed.")
        
        # Trip Decision Engine verification
        test_temporal_forecast_resolver_interpolation()
        print("✓ test_temporal_forecast_resolver_interpolation passed.")
        test_time_dependent_pfz_routing()
        print("✓ test_time_dependent_pfz_routing passed.")
        test_pfz_candidate_evaluation_and_ranking()
        print("✓ test_pfz_candidate_evaluation_and_ranking passed.")
        test_dynamic_temporal_wave_jump_routing()
        print("✓ test_dynamic_temporal_wave_jump_routing passed.")
        test_routing_with_zero_current()
        print("✓ test_routing_with_zero_current passed.")
        test_routing_extreme_wind_rejection()
        print("✓ test_routing_extreme_wind_rejection passed.")
        test_empty_pfz_advisory_handling()
        print("✓ test_empty_pfz_advisory_handling passed.")

        # PFZ Spatiotemporal Sampling Engine & INCOIS Endpoints (Milestone M2)
        test_enrich_point_schema()
        print("✓ test_enrich_point_schema passed.")
        test_enrich_point_bounds_validation()
        print("✓ test_enrich_point_bounds_validation passed.")
        test_enrich_point_grid_caching()
        print("✓ test_enrich_point_grid_caching passed.")
        test_enrich_pfz_linestring_sampling()
        print("✓ test_enrich_pfz_linestring_sampling passed.")
        test_enrich_pfz_multilinestring_sampling()
        print("✓ test_enrich_pfz_multilinestring_sampling passed.")
        test_enrich_pfz_degenerate_geometry()
        print("✓ test_enrich_pfz_degenerate_geometry passed.")
        test_enrich_pfz_geometry_hash_caching()
        print("✓ test_enrich_pfz_geometry_hash_caching passed.")
        test_catch_score_logic()
        print("✓ test_catch_score_logic passed.")
        test_enrich_feature_collection()
        print("✓ test_enrich_feature_collection passed.")
        test_point_analytics_endpoint()
        print("✓ test_point_analytics_endpoint passed.")
        test_pfz_lines_endpoint_enrichment()
        print("✓ test_pfz_lines_endpoint_enrichment passed.")
        test_multi_tier_failsafe_hierarchy()
        print("✓ test_multi_tier_failsafe_hierarchy passed.")
        # E2E Test Suite (Milestone M4 & M5)
        print("\nRunning comprehensive E2E test suite (Tiers 1-5)...")
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
        from tests.e2e.test_e2e_suite import run_suite
        e2e_res = run_suite()
        if e2e_res != 0:
            raise AssertionError("E2E test suite failed")
        
        print("\nAll backend and E2E tests passed successfully (100%)!")
    except AssertionError as e:
        print(f"FAIL: Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error occurred: {e}")
        sys.exit(1)
