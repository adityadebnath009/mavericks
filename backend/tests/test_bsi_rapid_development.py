import pytest
from datetime import datetime
from app.api.services.orca_bsi_engine import OrcaBsiEngine
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions, TimelineSeries

def test_rapid_development_scaling():
    engine = OrcaBsiEngine()
    
    # Create a snapshot with timeline data
    # Current Hs = 2.0
    # Past Hs (idx 3) = 1.0 -> 100% relative change!
    snapshot = EnvironmentSnapshot(
        current=EnvironmentalConditions(
            timestamp=datetime.now(),
            wave_height_m=2.0
        ),
        timeline=TimelineSeries(
            timestamps=[datetime.now(), datetime.now(), datetime.now(), datetime.now()],
            wave_height_m=[2.0, 1.8, 1.5, 1.0] 
        )
    )
    
    result = engine.calculate_rapid_development(snapshot)
    
    # 100% change > 30% threshold
    assert result["triggered"] is True
    # 1.0 / 1.0 = 1.0 severity capped
    assert result["severity"] == 1.0
    assert result["relative_change"] == 1.0
    
    # Test safe handling when timeline missing
    empty_snapshot = EnvironmentSnapshot(current=EnvironmentalConditions(timestamp=datetime.now(), wave_height_m=2.0))
    empty_result = engine.calculate_rapid_development(empty_snapshot)
    
    assert empty_result["triggered"] is False
    assert empty_result["severity"] == 0.0
