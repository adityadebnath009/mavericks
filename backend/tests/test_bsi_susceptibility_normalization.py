import pytest
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile, VesselProfile

def test_vessel_susceptibility_bounds():
    engine = OrcaBsiEngine()
    
    # 1. Neutral Vessel (15m) -> S_v should be exactly 1.0
    neutral_vessel = VesselProfile(length_m=15.0, beam_m=4.0, cruising_speed_kn=12.0)
    sv_neutral = engine.calculate_vessel_susceptibility(neutral_vessel)
    assert sv_neutral == 1.0, f"Expected 1.0 for neutral vessel, got {sv_neutral}"
    
    # 2. Small Vessel (5m) -> S_v should max out at bounded 1.2
    small_vessel = VesselProfile(length_m=5.0, beam_m=2.0, cruising_speed_kn=8.0)
    sv_small = engine.calculate_vessel_susceptibility(small_vessel)
    assert sv_small == 1.2, f"Expected small vessel to hit max bound 1.2, got {sv_small}"
    
    # 3. Large Vessel (30m) -> S_v should hit lower bound 0.8
    large_vessel = VesselProfile(length_m=30.0, beam_m=6.0, cruising_speed_kn=15.0)
    sv_large = engine.calculate_vessel_susceptibility(large_vessel)
    assert sv_large == 0.8, f"Expected large vessel to hit min bound 0.8, got {sv_large}"
    
    # 4. Strict Logic test: Small > Large
    assert sv_small > sv_large, "Small vessel susceptibility must be greater than large vessel"
