from datetime import datetime
from app.schemas.routing import RouteSnapshot, RouteSegment, RecommendedTrip, TripAnalysisResponse, AlternativeTrip
from app.core.enums import TripDecision, RiskLevel

def test_schema_serialization():
    # 1. Snapshot
    snap = RouteSnapshot(
        time=datetime(2026, 8, 26, 12, 0, 0),
        lat=15.0,
        lon=75.0,
        wave_height_m=2.5,
        wind_speed_kmh=18.0,
        wind_direction_deg=180.0,
        current_speed_ms=0.5,
        current_direction_deg=90.0,
        bsi=2,
        risk=RiskLevel.MODERATE
    )
    
    assert snap.model_dump()["risk"] == "MODERATE"
    assert snap.model_dump()["bsi"] == 2
    
    # 2. Segment
    seg = RouteSegment(
        segment_index=0,
        coordinates=[[75.0, 15.0], [75.1, 15.1]],
        risk=RiskLevel.MODERATE,
        reason="Elevated wave steepness"
    )
    
    assert seg.model_dump()["segment_index"] == 0
    assert len(seg.model_dump()["coordinates"]) == 2
    
    # 3. TripAnalysisResponse
    resp = TripAnalysisResponse(
        decision=TripDecision.CAUTION,
        recommended_pfz=RecommendedTrip(
            id="PFZ-1",
            travel_time_hours=10.5,
            route_coords=[[75.0, 15.0], [75.1, 15.1]],
            snapshots=[snap],
            segments=[seg]
        ),
        decision_reasons=[{"factor": "Safety", "detail": "Moderate wave height."}],
        alternatives=[AlternativeTrip(pfz_id="PFZ-2", status="REJECTED", reason="Too far.")]
    )
    
    dump = resp.model_dump()
    assert dump["decision"] == "CAUTION"
    assert dump["recommended_pfz"]["id"] == "PFZ-1"
    assert dump["alternatives"][0]["status"] == "REJECTED"
    print("✓ test_schema_serialization passed")

if __name__ == "__main__":
    test_schema_serialization()
    print("ALL SCHEMA TESTS PASSED")
