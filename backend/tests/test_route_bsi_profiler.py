import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile, VesselProfile
from app.api.services.route_bsi_profiler import RouteBsiProfiler, haversine_distance
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

class MockTimeline:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        
    def get_slice_at(self, eta: datetime):
        # Deterministic mock: changes hs based on hour offset to test temporal slicing
        # Let's say hs = 1.0 + (eta.hour % 24) * 0.1
        hs = 1.0 + (eta.hour % 24) * 0.1
        return EnvironmentSnapshot(
            current=EnvironmentalConditions(
                timestamp=eta,
                wave_height_m=hs,
                wind_wave_height_m=hs * 0.8,
                swell_wave_height_m=hs * 0.6,
                wave_period_s=6.0,
                wind_wave_direction_deg=0.0,
                swell_wave_direction_deg=90.0, # crossing sea to boost severity
                wave_direction_deg=45.0
            )
        )

class MockMarineForecastService:
    def __init__(self):
        self.call_count = 0
        self.requested_coords = []
        
    def get_environment(self, lat, lon, timestamp=None):
        self.call_count += 1
        self.requested_coords.append((lat, lon))
        return MockTimeline(lat, lon)

def test_eta_correctness():
    engine = OrcaBsiEngine()
    profiler = RouteBsiProfiler(MockMarineForecastService(), engine)
    vessel = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=10.0) # 10 kn = 18.52 km/h
    
    start_time = datetime(2026, 1, 1, 8, 0, 0)
    
    # Zero distance
    nodes = [{"lat": 15.0, "lon": 73.0}, {"lat": 15.0, "lon": 73.0}]
    profile = profiler.compute_etas(nodes, vessel, start_time)
    assert profile[0]["eta"] == profile[1]["eta"] == start_time
    
    # 18.52 km distance (approx 1 degree lon at equator is 111km, so let's just use exact math check)
    # Haversine distance between (15.0, 73.0) and (15.166, 73.0) is approx 18.46 km
    nodes2 = [{"lat": 15.0, "lon": 73.0}, {"lat": 15.166, "lon": 73.0}]
    profile2 = profiler.compute_etas(nodes2, vessel, start_time)
    dist = profile2[1]["distance_from_prev_km"]
    
    # Travel time should be exactly dist / 18.52 hours
    expected_hours = dist / 18.52
    expected_eta = start_time + timedelta(hours=expected_hours)
    
    assert abs((profile2[1]["eta"] - expected_eta).total_seconds()) < 1.0 # Within 1 second
    
    # Invalid speed
    vessel_invalid = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=0.0)
    with pytest.raises(ValueError):
        profiler.compute_etas(nodes2, vessel_invalid, start_time)

def test_spatial_deduplication():
    marine_service = MockMarineForecastService()
    engine = OrcaBsiEngine()
    profiler = RouteBsiProfiler(marine_service, engine)
    
    # Create 10 nodes that fall into exactly 3 rounded grid cells
    # Grid 1: (15.2, 73.8) -> nodes 0, 1, 2, 3
    # Grid 2: (15.3, 73.9) -> nodes 4, 5, 6
    # Grid 3: (15.4, 74.0) -> nodes 7, 8, 9
    
    nodes = [
        {"lat": 15.20, "lon": 73.80}, {"lat": 15.21, "lon": 73.81}, {"lat": 15.19, "lon": 73.79}, {"lat": 15.24, "lon": 73.84},
        {"lat": 15.30, "lon": 73.90}, {"lat": 15.31, "lon": 73.91}, {"lat": 15.29, "lon": 73.89},
        {"lat": 15.40, "lon": 74.00}, {"lat": 15.41, "lon": 74.01}, {"lat": 15.39, "lon": 73.99},
    ]
    
    vessel = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=10.0)
    start_time = datetime(2026, 1, 1, 8, 0, 0)
    
    # Running generation should fetch exactly 3 times
    profiler.generate_route_profile(nodes, vessel, start_time)
    assert marine_service.call_count == 3
    
def test_temporal_extraction_and_route_aggregation():
    marine_service = MockMarineForecastService()
    engine = OrcaBsiEngine()
    profiler = RouteBsiProfiler(marine_service, engine)
    
    nodes = [
        {"lat": 15.0, "lon": 73.0}, 
        {"lat": 15.166, "lon": 73.0}, # + ~1 hour
        {"lat": 15.332, "lon": 73.0}  # + ~1 hour
    ]
    vessel = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=10.0)
    start_time = datetime(2026, 1, 1, 8, 0, 0)
    
    result = profiler.generate_route_profile(nodes, vessel, start_time)
    
    # Verify temporal slicing was unique (environment should get worse each hour via our mock logic)
    sevs = [p["severity"] for p in result["profile"]]
    assert sevs[0] < sevs[1] < sevs[2], "Severities should increase over time due to deterministic mock"
    
    route_bsi = result["route_bsi"]
    assert route_bsi["maximum"] == result["profile"][-1]["bsi"]
    assert route_bsi["peak_node"] == 2
    
def test_departure_optimizer():
    marine_service = MockMarineForecastService()
    engine = OrcaBsiEngine()
    profiler = RouteBsiProfiler(marine_service, engine)
    
    nodes = [{"lat": 15.0, "lon": 73.0}]
    vessel = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=10.0)
    start_time = datetime(2026, 1, 1, 8, 0, 0)
    
    # We mock generate_route_profile to return specific peaks to test the objective function
    profiler.generate_route_profile = MagicMock(side_effect=[
        {"route_bsi": {"maximum": 40, "mean_severity": 20}},
        {"route_bsi": {"maximum": 45, "mean_severity": 25}},
        {"route_bsi": {"maximum": 51, "mean_severity": 30}},
        {"route_bsi": {"maximum": 63, "mean_severity": 40}},
    ])
    
    # Deteriorating conditions: optimizer should pick T+0 (08:00)
    res_deteriorating = profiler.optimize_departure(nodes, vessel, start_time)
    assert res_deteriorating["recommended_departure"] == start_time.isoformat()
    
    # Improving conditions
    profiler.generate_route_profile = MagicMock(side_effect=[
        {"route_bsi": {"maximum": 82, "mean_severity": 60}},
        {"route_bsi": {"maximum": 76, "mean_severity": 55}},
        {"route_bsi": {"maximum": 58, "mean_severity": 40}},
        {"route_bsi": {"maximum": 43, "mean_severity": 20}},
    ])
    
    # Improving conditions: optimizer should pick T+3 (11:00)
    res_improving = profiler.optimize_departure(nodes, vessel, start_time)
    expected_best = (start_time + timedelta(hours=3)).isoformat()
    assert res_improving["recommended_departure"] == expected_best

def test_high_severity_duration():
    marine_service = MockMarineForecastService()
    engine = OrcaBsiEngine()
    profiler = RouteBsiProfiler(marine_service, engine)
    
    # 3 nodes, 1 hour apart each.
    # Total trip = 2 hours.
    nodes = [
        {"lat": 15.0, "lon": 73.0}, 
        {"lat": 15.166, "lon": 73.0}, # T+1
        {"lat": 15.332, "lon": 73.0}  # T+2
    ]
    vessel = VesselProfile(length_m=10.0, beam_m=3.0, cruising_speed_kn=10.0)
    start_time = datetime(2026, 1, 1, 8, 0, 0)
    
    # Mock evaluate to control exact severities
    # N0: 30, N1: 65, N2: 80
    profiler.bsi_engine.evaluate = MagicMock(side_effect=[
        {"severity_score": 30, "bsi": 2},
        {"severity_score": 65, "bsi": 4},
        {"severity_score": 80, "bsi": 6},
    ])
    
    res = profiler.generate_route_profile(nodes, vessel, start_time)
    
    # High severity nodes: N1 (at T+1) and N2 (at T+2).
    # Duration = (N1_eta - N0_eta) + (N2_eta - N1_eta) ? 
    # The logic adds the delta from prev node.
    # N1 adds 1 hr. N2 adds 1 hr. Total = 2 hrs.
    assert res["route_bsi"]["high_severity_duration_hours"] > 0
