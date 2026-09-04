import pytest
from app.api.services.orca_bsi_engine import OrcaBsiEngine

def test_heading_boundaries():
    engine = OrcaBsiEngine()
    
    # 1. Head Seas (0)
    res_0 = engine.calculate_wave_heading(45.0, 45.0)
    assert res_0["relative_angle_deg"] == 0.0
    assert res_0["modifier"] == 1.0
    assert res_0["condition"] == "head/following"

    # 2. 45 degrees
    res_45 = engine.calculate_wave_heading(45.0, 90.0)
    assert res_45["relative_angle_deg"] == 45.0
    assert res_45["modifier"] > 1.0 and res_45["modifier"] < 1.25

    # 3. Beam Seas (90) - Should be max modifier 1.25
    res_90 = engine.calculate_wave_heading(0.0, 90.0)
    assert res_90["relative_angle_deg"] == 90.0
    assert res_90["modifier"] == 1.25
    assert res_90["condition"] == "beam"

    # 4. 135 degrees
    res_135 = engine.calculate_wave_heading(0.0, 135.0)
    assert res_135["relative_angle_deg"] == 135.0
    assert res_135["modifier"] == res_45["modifier"]

    # 5. Following Seas (180)
    res_180 = engine.calculate_wave_heading(0.0, 180.0)
    assert res_180["relative_angle_deg"] == 180.0
    assert res_180["modifier"] == 1.0

    # 6. Wrap around (359)
    res_359 = engine.calculate_wave_heading(0.0, 359.0)
    assert res_359["relative_angle_deg"] == 1.0
    assert res_359["modifier"] < 1.05
