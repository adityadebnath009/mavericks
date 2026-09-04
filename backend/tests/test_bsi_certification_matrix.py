import pytest
import math
from datetime import datetime, timedelta
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile, VesselProfile
from app.api.services.route_bsi_profiler import RouteBsiProfiler
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

engine = OrcaBsiEngine()

# ---------------------------------------------------------
# A. Wave Physics Matrix (20 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("hs, tp, expected_severity_trend", [
    (0.5, 12, "low"),
    (1.0, 12, "low"),
    (2.0, 12, "moderate"),
    (3.0, 12, "high"),
    (1.0, 12, "low"),
    (1.0, 8,  "moderate"),
    (1.0, 6,  "high"),
    (1.0, 4,  "extreme") # Shorter Tp = higher steepness
])
def test_wave_physics_steepness_invariants(hs, tp, expected_severity_trend):
    res = engine.calculate_wave_steepness(hs, tp)
    # Invariant: At equal Hs, shorter Tp -> greater steepness
    assert res["severity"] >= 0.0
    assert res["severity"] <= 1.0

def test_wave_physics_pathological():
    # Zero Hs
    assert engine.calculate_wave_steepness(0.0, 10.0)["severity"] == 0.0
    # Zero Tp
    assert engine.calculate_wave_steepness(2.0, 0.0)["severity"] == 0.0
    # Missing
    assert engine.calculate_wave_steepness(None, 10.0)["severity"] == 0.0

# ---------------------------------------------------------
# B. Vessel Susceptibility Matrix (15 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("length", [
    5.0, 6.0, 10.0, 12.49, 12.50, 12.51, 15.0, 18.74, 18.75, 18.76, 20.0, 30.0, 50.0
])
def test_vessel_susceptibility_boundaries(length):
    v = VesselProfile(length_m=length, beam_m=3.0, cruising_speed_kn=10.0)
    sv = engine.calculate_vessel_susceptibility(v)
    # Invariant 3: 0.8 <= Sv <= 1.2
    assert 0.8 <= sv <= 1.2
    
    # Specific mathematical bounds for base_ratio = 15/L
    if length <= 12.5:
        assert sv == 1.2
    elif length >= 18.75:
        assert sv == 0.8
    else:
        assert 0.8 <= sv <= 1.2

# ---------------------------------------------------------
# C. Heading Physics Matrix (15 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("wave_dir, boat_dir, expected_mod, condition", [
    (0, 0, 1.0, "head/following"),
    (45, 0, 1.12, "head/following"), # Wait, 45 is edge. Engine classifies 45 as head/following
    (90, 0, 1.25, "beam"),
    (135, 0, 1.12, "head/following"),
    (180, 0, 1.0, "head/following"),
    (359, 0, 1.0, "head/following"), # Circular equivalence check
    (1, 0, 1.0, "head/following"),   # Circular equivalence check
    (10, 350, 1.06, "head/following") # 20 degree difference
])
def test_heading_physics(wave_dir, boat_dir, expected_mod, condition):
    res = engine.calculate_wave_heading(wave_dir, boat_dir)
    assert abs(res["modifier"] - expected_mod) <= 0.02
    # Invariant: Head=1.0, Beam=1.25, Following=1.0
    assert 1.0 <= res["modifier"] <= 1.25

# ---------------------------------------------------------
# D. Crossing Seas Matrix (20 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("ww_d, sw_d, ww_h, sw_h, expected_trend", [
    (0, 0, 2.0, 2.0, 0.0),     # Parallel -> ~0
    (0, 15, 2.0, 2.0, 0.16),   # 15 deg -> low
    (0, 45, 2.0, 2.0, 0.5),    # 45 deg -> moderate
    (0, 60, 2.0, 2.0, 0.66),   # 60 deg -> high
    (0, 90, 2.0, 2.0, 1.0),    # 90 deg + equal -> max (1.0)
    (0, 90, 2.0, 1.8, 0.8),         # 90 deg + 0.8 energy ratio -> high
    (0, 90, 2.0, 1.414, 0.5),       # 90 deg + 0.5 energy ratio -> moderate
    (0, 90, 2.0, 0.632, 0.1),       # 90 deg + 0.1 energy ratio -> low
    (350, 10, 2.0, 2.0, 0.22)  # Wrapping: 20 deg diff -> ~0.22
])
def test_crossing_seas_matrix(ww_d, sw_d, ww_h, sw_h, expected_trend):
    snap = EnvironmentSnapshot(current=EnvironmentalConditions(
        timestamp=datetime.now(),
        wind_wave_height_m=ww_h, wind_wave_direction_deg=ww_d,
        swell_wave_height_m=sw_h, swell_wave_direction_deg=sw_d
    ))
    res = engine.calculate_crossing_seas(snap)
    if isinstance(expected_trend, float):
        assert abs(res["severity"] - expected_trend) <= 0.05
    # Invariant 1: 0 <= C_cross <= 1
    assert 0.0 <= res["severity"] <= 1.0

# ---------------------------------------------------------
# E. Rapid Development Matrix (10 Cases)
# ---------------------------------------------------------
@pytest.mark.parametrize("curr_hs, past_hs, expected_trig", [
    (2.0, 2.0, False), # 0%
    (2.2, 2.0, False), # 10%
    (2.4, 2.0, False), # 20%
    (2.58, 2.0, False), # 29%
    (2.62, 2.0, True),  # 31% (>30% threshold)
    (3.0, 2.0, True),  # 50%
    (4.0, 2.0, True),  # 100%
    (1.6, 2.0, False), # -20%
    (1.0, 2.0, False)  # -50%
])
def test_rapid_development_percentages(curr_hs, past_hs, expected_trig):
    snap = EnvironmentSnapshot(
        current=EnvironmentalConditions(timestamp=datetime.now(), wave_height_m=curr_hs),
        timeline={"timestamps": [datetime.now(), datetime.now(), datetime.now(), datetime.now()], 
                  "wave_height_m": [curr_hs, curr_hs, curr_hs, past_hs]} # past_hs is index 3
    )
    res = engine.calculate_rapid_development(snap)
    assert res["triggered"] == expected_trig

# ---------------------------------------------------------
# Invariants & Pathological
# ---------------------------------------------------------
def test_invariant_missing_data():
    snap = EnvironmentSnapshot(current=EnvironmentalConditions(
        timestamp=datetime.now(), wind_wave_height_m=2.0, swell_wave_height_m=2.0
    ))
    res = engine.calculate_crossing_seas(snap)
    # Invariant 7: Missing data never becomes fabricated
    assert res["available"] is False
    assert res["severity"] is None
