import pytest
import datetime
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.orca_bsi_engine import VesselProfile
from app.api.endpoints.geofence import get_geofence_geojson

def test_geofence_endpoint_is_instant_and_offline():
    """
    Test that the geofence endpoint returns the fallback instantly
    without hitting Postgres, preventing Uvicorn thread locks.
    """
    import time
    t0 = time.time()
    res = get_geofence_geojson()
    t1 = time.time()
    
    assert res is not None
    assert "type" in res
    assert res["type"] == "FeatureCollection"
    # Must return in under 0.1 seconds, proving it's offline/cached.
    assert (t1 - t0) < 0.1

def test_routing_rejects_future_dates_beyond_72h():
    """
    Ensure the routing engine strictly rejects departure times
    that exceed the 72-hour forecast window to prevent hallucinated weather.
    """
    vessel = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
    
    # 4 days in the future
    future_time = (datetime.datetime.utcnow() + datetime.timedelta(days=4)).isoformat() + "Z"
    
    with pytest.raises(Exception, match="outside the 72-hour forecast window"):
        PFZRoutingService.calculate_optimal_route(
            start_lat=20.5,
            start_lon=88.5,
            end_lat=16.0,
            end_lon=83.5,
            vessel_profile=vessel,
            departure_time=future_time
        )

def test_routing_accepts_valid_future_time():
    """
    Ensure the routing engine successfully plans routes within
    the valid 72-hour forecast window.
    """
    vessel = VesselProfile(length_m=10.0, beam_m=3.5, cruising_speed_kn=10.0)
    
    # 2 hours in the future
    valid_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).isoformat() + "Z"
    
    try:
        res = PFZRoutingService.calculate_optimal_route(
            start_lat=20.59,
            start_lon=88.36,
            end_lat=16.07,
            end_lon=84.25,
            vessel_profile=vessel,
            departure_time=valid_time
        )
        assert res is not None
        assert "path" in res
    except Exception as e:
        pytest.fail(f"Valid future time threw an exception: {e}")
