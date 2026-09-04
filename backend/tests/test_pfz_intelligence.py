from app.api.services.pfz_intelligence import PFZIntelligenceService, haversine_distance

def test_haversine_distance():
    """
    Validates the Haversine distance formula with known values.
    """
    # Distance between Mumbai (18.97, 72.82) and Alibag (18.66, 72.87) is ~35 km
    dist = haversine_distance(18.97, 72.82, 18.66, 72.87)
    assert 30.0 <= dist <= 40.0

def test_pfz_evaluation():
    """
    Verifies the Shapely-based nearest point calculations and risk evaluation
    for an actual PFZ line feature.
    """
    # Vessel coordinates near Mumbai
    v_lat = 19.5
    v_lon = 72.0
    pfz_id = "pfzlines.1"
    
    res = PFZIntelligenceService.evaluate_pfz_zone(
        vessel_lat=v_lat,
        vessel_lon=v_lon,
        pfz_id=pfz_id,
        beam_m=3.5
    )
    
    assert res is not None
    assert res["pfz_id"] == pfz_id
    assert "distance_km" in res
    assert isinstance(res["distance_km"], float)
    assert res["distance_km"] >= 0.0
    
    # Check nearest point output
    assert "nearest_point" in res
    assert "latitude" in res["nearest_point"]
    assert "longitude" in res["nearest_point"]
    
    # Check marine conditions properties
    assert "marine_conditions" in res
    conds = res["marine_conditions"]
    assert "wave_height_m" in conds
    assert "wind_speed_kmh" in conds
    assert "current_speed_ms" in conds
    assert "wave_steepness" in conds
    
    # Check independent safety risk properties (concept separation)
    assert "marine_risk" in res
    assert "rating" in res["marine_risk"]
    assert res["marine_risk"]["rating"] in ["LOW", "MODERATE", "HIGH"]
    assert "reasons" in res["marine_risk"]
    assert len(res["marine_risk"]["reasons"]) > 0

def test_pfz_invalid_id():
    """
    Asserts that looking up a non-existent PFZ feature raises a ValueError.
    """
    try:
        PFZIntelligenceService.evaluate_pfz_zone(
            vessel_lat=15.0,
            vessel_lon=72.0,
            pfz_id="pfzlines.nonexistent_id",
            beam_m=3.5
        )
        assert False, "Should have raised ValueError for invalid ID"
    except ValueError as e:
        assert "not found" in str(e)


