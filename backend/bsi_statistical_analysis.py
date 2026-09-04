import pandas as pd
import numpy as np
import math
from datetime import datetime
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

def run_stats():
    print("Loading historical data...")
    df = pd.read_csv('/Users/adityadebnath/Downloads/indian_coastal_marine_dataset_2020_2025 (2).csv')
    
    # 1. Prepare raw data for percentiles
    hs_array = df['wave_height_m'].fillna(0.0).values
    tp_array = df['wave_period_s'].fillna(6.0).values
    
    g = 9.81
    with np.errstate(divide='ignore', invalid='ignore'):
        steepness = (2 * math.pi * hs_array) / (g * (tp_array ** 2))
        steepness[~np.isfinite(steepness)] = 0.0
        steepness[steepness < 0] = 0.0

    # Percentiles
    hs_p = np.percentile(hs_array, [50, 90, 95, 99])
    mu_p = np.percentile(steepness, [50, 90, 95, 99])
    
    print("\n--- 1. Hs Distribution ---")
    print(f"Min: {np.min(hs_array):.2f}, Median: {hs_p[0]:.2f}, P90: {hs_p[1]:.2f}, P95: {hs_p[2]:.2f}, P99: {hs_p[3]:.2f}, Max: {np.max(hs_array):.2f}")
    
    print("\n--- 2. Steepness Distribution ---")
    print(f"Min: {np.min(steepness):.4f}, Median: {mu_p[0]:.4f}, P90: {mu_p[1]:.4f}, P95: {mu_p[2]:.4f}, P99: {mu_p[3]:.4f}, Max: {np.max(steepness):.4f}")

    # 3. Histogram
    base_hs_sev = np.clip(hs_array / 4.0, 0, 1)
    mu_sev = np.clip(steepness / 0.08, 0, 1)
    
    # Matching the v2.2 engine logic exactly: (base + steep + rapid_dev + crossing) / 4.0
    # In historical offline data: rapid_dev=0 (no timeline) and crossing=0 (missing partition)
    env_sev = np.clip(base_hs_sev + mu_sev, 0, 1.0) 
    total_sev = np.clip(env_sev * 1.2 * 100, 0, 100).astype(int) # sv=1.2 for 12m vessel
    
    print("\n--- 3. Raw Severity Histogram ---")
    hist, bins = np.histogram(total_sev, bins=range(0, 110, 10))
    max_count = max(hist) if max(hist) > 0 else 1
    for i in range(len(hist)):
        bar_len = int((hist[i] / max_count) * 20)
        bar = "█" * bar_len
        print(f"{bins[i]:2d}-{bins[i+1]-1:2d} | {hist[i]:8d} | {bar}")

    # 4. Top 100 Analysis
    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=12.0, beam_m=3.0, cruising_speed_kn=10.0)
    
    df['steepness'] = steepness
    top_100_hs = df.nlargest(100, 'wave_height_m').to_dict('records')
    top_100_mu = df.nlargest(100, 'steepness').to_dict('records')
    
    def eval_row(row):
        snap = EnvironmentSnapshot(current=EnvironmentalConditions(
            timestamp=datetime.now(),
            wave_height_m=float(row.get('wave_height_m', 0.0)),
            wave_period_s=float(row.get('wave_period_s', 6.0))
        ))
        return engine.evaluate(snap, vessel)
        
    print("\n--- 4. Worst 100 by Hs ---")
    hs_sevs = [eval_row(r)['severity_score'] for r in top_100_hs]
    print(f"Top 100 Hs Range: {top_100_hs[-1]['wave_height_m']:.2f}m to {top_100_hs[0]['wave_height_m']:.2f}m")
    print(f"Resulting Severity - Min: {min(hs_sevs)}, Median: {np.median(hs_sevs)}, Max: {max(hs_sevs)}")
    
    print("\n--- 5. Worst 100 by Steepness ---")
    mu_sevs = [eval_row(r)['severity_score'] for r in top_100_mu]
    print(f"Top 100 Steepness Range: {top_100_mu[-1]['steepness']:.4f} to {top_100_mu[0]['steepness']:.4f}")
    print(f"Resulting Severity - Min: {min(mu_sevs)}, Median: {np.median(mu_sevs)}, Max: {max(mu_sevs)}")

if __name__ == "__main__":
    run_stats()
