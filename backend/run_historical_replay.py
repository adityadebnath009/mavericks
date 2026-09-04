import pandas as pd
from collections import Counter
from datetime import datetime
import time
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.core.domain import EnvironmentSnapshot, EnvironmentalConditions

def run_replay():
    print("Loading historical Indian Marine Data...")
    try:
        df = pd.read_csv('/Users/adityadebnath/Downloads/indian_coastal_marine_dataset_2020_2025 (2).csv')
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        return

    total_records = len(df)
    print(f"Total historical records: {total_records}")
    
    engine = OrcaBsiEngine()
    vessel = VesselProfile(length_m=12.0, beam_m=3.0, cruising_speed_kn=10.0)
    
    bsi_distribution = Counter()
    severity_distribution = {"0-20 (Safe)": 0, "21-50 (Moderate)": 0, "51-75 (High)": 0, "76-100 (Extreme)": 0}
    
    missing_data_count = 0
    crossing_sea_count = 0
    
    print(f"Running Engine against ALL {total_records} historical points (optimized loop)...")
    start_time = time.time()
    
    # Optimize by converting to dicts
    records = df.to_dict('records')
    timestamp_now = datetime.now()
    
    for row in records:
        hs = row.get('wave_height_m')
        tp = row.get('wave_period_s')
        
        ww_h = row.get('wind_wave_height_m', None)
        ww_d = row.get('wind_wave_direction_deg', None)
        sw_h = row.get('swell_height_m', None)
        sw_d = row.get('swell_direction_deg', None)
        
        if pd.isna(ww_h) or pd.isna(ww_d) or pd.isna(sw_h) or pd.isna(sw_d):
            missing_data_count += 1
            
        snap = EnvironmentSnapshot(
            current=EnvironmentalConditions(
                timestamp=timestamp_now,
                wave_height_m=float(hs) if pd.notna(hs) else 0.0,
                wave_period_s=float(tp) if pd.notna(tp) else 6.0,
                wind_wave_height_m=float(ww_h) if pd.notna(ww_h) else None,
                wind_wave_direction_deg=float(ww_d) if pd.notna(ww_d) else None,
                swell_wave_height_m=float(sw_h) if pd.notna(sw_h) else None,
                swell_wave_direction_deg=float(sw_d) if pd.notna(sw_d) else None,
            )
        )
        
        res = engine.evaluate(snap, vessel)
        
        bsi = res["bsi"]
        sev = res["severity_score"]
        
        bsi_distribution[bsi] += 1
        
        if sev <= 20: severity_distribution["0-20 (Safe)"] += 1
        elif sev <= 50: severity_distribution["21-50 (Moderate)"] += 1
        elif sev <= 75: severity_distribution["51-75 (High)"] += 1
        else: severity_distribution["76-100 (Extreme)"] += 1
        
        if res["hazards"]["crossing_sea"].get("triggered"):
            crossing_sea_count += 1
            
    elapsed = time.time() - start_time
    print(f"\nProcessed {total_records} records in {elapsed:.1f} seconds.")
    print("\n--- FULL BSI REPLAY RESULTS ---")
    print("BSI Hazard Bitmask Distribution:")
    for k, v in sorted(bsi_distribution.items()):
        print(f"  BSI {k}: {v} cases ({round(v/total_records*100, 3)}%)")
        
    print("\nSeverity Distribution:")
    for k, v in severity_distribution.items():
        print(f"  {k}: {v} cases ({round(v/total_records*100, 3)}%)")
        
    print(f"\nMissing Wind/Swell Data Rate: {round(missing_data_count/total_records*100, 3)}%")
    print(f"Crossing Seas Triggered: {crossing_sea_count} cases")
    print("--------------------------\n")

if __name__ == "__main__":
    run_replay()
