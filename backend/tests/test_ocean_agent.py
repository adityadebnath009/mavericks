import numpy as np
from app.agents.ocean_agent import OceanAnalyticsAgent

def test_advanced_ocean_agent():
    print("=== Testing Advanced Ocean Analytics Agent ===")
    agent = OceanAnalyticsAgent()

    # Create 10x10 synthetic grids
    print("\n[1] Generating synthetic ocean grids...")
    
    # Chlorophyll: Baseline 0.2 mg/m^3, with a bloom of 2.0 mg/m^3 on the right half
    chlorophyll = np.full((10, 10), 0.2)
    chlorophyll[:, 5:] = 2.0
    
    # SST: Baseline 25.0C, hitting a warm front of 28.0C on the right half
    # This creates a sharp vertical edge right down the middle (column index 4 to 5)
    sst = np.full((10, 10), 25.0)
    sst[:, 5:] = 28.0
    
    # Calm sea state (wave heights around 0.5m)
    waves = np.random.uniform(0.3, 0.7, (10, 10))
    
    time_factor = 1.0 

    print("[2] Running Advanced PFZ Scoring...")
    pfz_scores, coincidence, hsi_maps = agent.score_fishing_grounds(
        chlorophyll, sst, waves, time_factor
    )
    
    print("\n--- Results ---")
    best_pfz = np.max(pfz_scores)
    best_loc = np.unravel_index(np.argmax(pfz_scores), pfz_scores.shape)
    
    # The best location should fall exactly on the boundary column where gradients intersect
    print(f"Max PFZ Probability: {best_pfz:.2f} at grid index {best_loc}")
    
    max_edge = np.max(coincidence)
    print(f"Max Thermal-Chlorophyll Coincidence Edge: {max_edge:.2f}")

    print("\nHabitat Suitability Indices (HSI) Maximums:")
    for species, hsi_grid in hsi_maps.items():
        print(f" - {species}: {np.max(hsi_grid):.2f}")

    # Assertions to prove the spatial math works
    assert max_edge > 0.0, "Coincidence edge should be detected where fronts overlap."
    assert "Yellowfin Tuna" in hsi_maps, "Species HSI map missing."
    print("\n✅ All spatial gradients, coincidence edges, and HSI calculations executed successfully.")

if __name__ == "__main__":
    test_advanced_ocean_agent()