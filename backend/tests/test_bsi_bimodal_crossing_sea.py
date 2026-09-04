import pytest
from datetime import datetime
from app.api.services.orca_bsi_engine import OrcaBsiEngine
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

def create_env(ww_h, ww_d, sw_h, sw_d):
    return EnvironmentSnapshot(
        current=EnvironmentalConditions(
            timestamp=datetime.now(),
            wind_wave_height_m=ww_h,
            wind_wave_direction_deg=ww_d,
            swell_wave_height_m=sw_h,
            swell_wave_direction_deg=sw_d
        )
    )

def test_bimodal_crossing_physics():
    engine = OrcaBsiEngine()
    
    # 1. Maximum severity at 90 deg + equal energy
    snap_max = create_env(ww_h=2.0, ww_d=0.0, sw_h=2.0, sw_d=90.0)
    res_max = engine.calculate_crossing_seas(snap_max)
    assert res_max["severity"] == 1.0, f"Expected 1.0, got {res_max['severity']}"
    assert res_max["triggered"] is True
    assert res_max["angular_separation_deg"] == 90.0
    
    # 2. Near-zero for parallel systems (0 deg difference)
    snap_parallel = create_env(ww_h=2.0, ww_d=45.0, sw_h=2.0, sw_d=45.0)
    res_parallel = engine.calculate_crossing_seas(snap_parallel)
    assert res_parallel["severity"] == 0.0
    assert res_parallel["triggered"] is False
    
    # 3. Low severity for severely imbalanced systems
    # Even if 90 degrees apart, if one wave is tiny, severity is low.
    snap_imbalanced = create_env(ww_h=0.2, ww_d=0.0, sw_h=3.0, sw_d=90.0)
    res_imb = engine.calculate_crossing_seas(snap_imbalanced)
    # ww_e = 0.04, sw_e = 9.0 -> ratio = 0.04 / 9.0 = 0.0044
    assert res_imb["severity"] < 0.05
    assert res_imb["triggered"] is False
    assert res_imb["energy_ratio"] < 0.01
