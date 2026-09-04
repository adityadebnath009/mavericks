import pytest
from datetime import datetime
from app.api.services.orca_bsi_engine import OrcaBsiEngine
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

def test_missing_data_discipline():
    engine = OrcaBsiEngine()
    
    # Missing directional parameters completely
    snap_missing = EnvironmentSnapshot(
        current=EnvironmentalConditions(
            timestamp=datetime.now(),
            wind_wave_height_m=2.0,
            swell_wave_height_m=2.0,
            # Directions are missing/None
            wind_wave_direction_deg=None,
            swell_wave_direction_deg=None
        )
    )
    
    res = engine.calculate_crossing_seas(snap_missing)
    
    # Ensure it returns unavailable gracefully instead of assuming 0 deg
    assert res["available"] is False
    assert res["severity"] is None
    assert res["reason"] == "wind-sea/swell directional data unavailable"
    
    # Also test heading calculation missing
    heading_res = engine.calculate_wave_heading(None, 45.0)
    assert heading_res["available"] is False
    assert heading_res["modifier"] == 1.0  # Fallback neutral
    assert heading_res["relative_angle_deg"] is None
