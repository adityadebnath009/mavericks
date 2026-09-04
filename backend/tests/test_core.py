from app.core.exceptions import DataUnavailableError
from app.core.enums import TripDecision, RiskLevel

def test_data_unavailable_error():
    try:
        raise DataUnavailableError("Geofence API is offline")
    except DataUnavailableError as e:
        assert str(e) == "Geofence API is offline"
        assert isinstance(e, Exception)
    print("✓ test_data_unavailable_error passed")

def test_trip_decision_enum():
    assert TripDecision.INVALID_REQUEST.value == "INVALID_REQUEST"
    assert TripDecision.DATA_UNAVAILABLE.value == "DATA_UNAVAILABLE"
    assert TripDecision.REJECTED_NO_SAFE_ROUTE.value == "REJECTED_NO_SAFE_ROUTE"
    assert TripDecision.CAUTION.value == "CAUTION"
    assert TripDecision.RECOMMENDED.value == "RECOMMENDED"
    print("✓ test_trip_decision_enum passed")

def test_risk_level_enum():
    assert RiskLevel.LOW.value == "LOW"
    assert RiskLevel.MODERATE.value == "MODERATE"
    assert RiskLevel.HIGH.value == "HIGH"
    assert RiskLevel.EXTREME.value == "EXTREME"
    print("✓ test_risk_level_enum passed")

if __name__ == "__main__":
    test_data_unavailable_error()
    test_trip_decision_enum()
    test_risk_level_enum()
    print("ALL CORE TESTS PASSED")
