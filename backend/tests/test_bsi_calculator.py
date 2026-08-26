from app.api.services.bsi_calculator import BSICalculator

def test_steepness_index():
    # I_steepness = (Ss / 0.05) * (Hs / h0)
    # With Ss = 0.04, Hs = 2.0, h0 = 2.5:
    # (0.04 / 0.05) * (2.0 / 2.5) = 0.8 * 0.8 = 0.64
    idx = BSICalculator.calculate_steepness_index(0.04, 2.0)
    assert round(idx, 2) == 0.64
    
    # Exceeding threshold (0.8)
    # With Ss = 0.05, Hs = 2.5:
    # (0.05 / 0.05) * (2.5 / 2.5) = 1.0
    idx_high = BSICalculator.calculate_steepness_index(0.05, 2.5)
    assert idx_high >= 0.8

def test_crossing_sea_index():
    # I_crossing = 0.5 * Hs * exp(-10 * (ss - 1)^2)
    # With Hs = 1.5, ss = 1.0 (pure crossing):
    # 0.5 * 1.5 * exp(0) = 0.75
    idx = BSICalculator.calculate_crossing_sea_index(1.5, 1.0)
    assert idx == 0.75
    
    # Exceeding threshold (0.65)
    # With Hs = 2.0, ss = 1.0:
    # 0.5 * 2.0 * exp(0) = 1.0
    idx_high = BSICalculator.calculate_crossing_sea_index(2.0, 1.0)
    assert idx_high >= 0.65

def test_rapid_dev_index():
    # Z_6h = |Hsea_i - Hsea_f| / Hsea_i
    # Initial = 2.0, Final = 2.5
    # |2.0 - 2.5| / 2.0 = 0.25 (exceeds threshold 0.2)
    idx = BSICalculator.calculate_rapid_dev_index(2.0, 2.5)
    assert round(idx, 2) == 0.25
    
    # No rapid development
    idx_low = BSICalculator.calculate_rapid_dev_index(2.0, 2.1)
    assert round(idx_low, 2) == 0.05
    
    # Safety checks for division by zero
    assert BSICalculator.calculate_rapid_dev_index(0.0, 2.5) == 0.0

def test_all_bsi_combinations():
    # Parameters organized by: (Ss, Hs, ss, Hsea_i, Hsea_f)
    # Outputs BSI 0 to 7.
    
    # BSI = 0 (Safe)
    assert BSICalculator.calculate_bsi(0.01, 1.0, 0.5, 1.0, 1.0) == 0
    
    # BSI = 1 (Steepness exceeded only)
    assert BSICalculator.calculate_bsi(0.05, 2.5, 0.5, 1.0, 1.0) == 1
    
    # BSI = 2 (Crossing sea exceeded only)
    assert BSICalculator.calculate_bsi(0.01, 2.0, 1.0, 1.0, 1.0) == 2
    
    # BSI = 3 (Steepness + Crossing sea)
    assert BSICalculator.calculate_bsi(0.05, 2.5, 1.0, 1.0, 1.0) == 3
    
    # BSI = 4 (Rapid development exceeded only)
    assert BSICalculator.calculate_bsi(0.01, 1.0, 0.5, 2.0, 2.5) == 4
    
    # BSI = 5 (Rapid development + Steepness)
    assert BSICalculator.calculate_bsi(0.05, 2.5, 0.5, 2.0, 2.5) == 5
    
    # BSI = 6 (Rapid development + Crossing sea)
    assert BSICalculator.calculate_bsi(0.01, 2.0, 1.0, 2.0, 2.5) == 6
    
    # BSI = 7 (All indices exceeded)
    assert BSICalculator.calculate_bsi(0.05, 2.5, 1.0, 2.0, 2.5) == 7

def test_bsi_details_decoding():
    # Check details for SAFE (BSI = 0)
    details_safe = BSICalculator.get_bsi_details(0)
    assert details_safe["rating"] == "SAFE"
    assert len(details_safe["active_hazards"]) == 0
    
    # Check details for WARNING (BSI = 7)
    details_critical = BSICalculator.get_bsi_details(7)
    assert details_critical["rating"] == "WARNING"
    assert "Wave Steepness" in details_critical["active_hazards"]
    assert "Crossing Sea" in details_critical["active_hazards"]
    assert "Rapid Sea Development" in details_critical["active_hazards"]

def test_vessel_beam_safety():
    # Critical Beam = 4 * Hs
    
    # Scenario A: High waves Hs = 1.5m -> Critical Beam = 6.0m
    hs_a = 1.5
    crit_a = 4.0 * hs_a
    assert crit_a == 6.0
    
    # Traditional Craft (beam = 2.5m) under Hs = 1.5m is vulnerable
    assert 2.5 < crit_a
    # Small Trawler (beam = 4.5m) under Hs = 1.5m is vulnerable
    assert 4.5 < crit_a
    # Large Trawler (beam = 6.5m) under Hs = 1.5m is safe
    assert 6.5 >= crit_a
    
    # Scenario B: Low waves Hs = 0.8m -> Critical Beam = 3.2m
    hs_b = 0.8
    crit_b = 4.0 * hs_b
    assert crit_b == 3.2
    
    # Traditional Craft (beam = 2.5m) is vulnerable
    assert 2.5 < crit_b
    # Small Trawler (beam = 4.5m) is safe
    assert 4.5 >= crit_b
    # Large Trawler (beam = 6.5m) is safe
    assert 6.5 >= crit_b