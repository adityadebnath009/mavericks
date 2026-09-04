import pandas as pd
import math
import numpy as np

def run():
    print("Loading dataset for extreme event forensics...")
    df = pd.read_csv('/Users/adityadebnath/Downloads/indian_coastal_marine_dataset_2020_2025 (2).csv')
    df['datetime_dt'] = pd.to_datetime(df['datetime'])
    
    # Calculate steepness
    g = 9.81
    with np.errstate(divide='ignore', invalid='ignore'):
        steep = (2 * math.pi * df['wave_height_m'].fillna(0.0)) / (g * (df['wave_period_s'].fillna(6.0) ** 2))
        steep = steep.fillna(0.0)
        steep[steep < 0] = 0.0
        steep[~np.isfinite(steep)] = 0.0
    df['steepness'] = steep
    
    # 1. Extreme Hs excluding May 2020 (Amphan)
    not_amphan = df[~((df['datetime_dt'].dt.year == 2020) & (df['datetime_dt'].dt.month == 5))]
    top_hs = not_amphan.nlargest(5, 'wave_height_m')
    
    print("\n--- 1. Extreme Wave Heights (Excluding May 2020) ---")
    print(top_hs[['datetime', 'latitude', 'longitude', 'wave_height_m', 'wind_speed_kts', 'air_pressure_hpa']].to_string(index=False))
    
    # 2. Extreme Wind Speeds excluding May 2020
    top_wind = not_amphan.nlargest(5, 'wind_speed_kts')
    print("\n--- 2. Extreme Wind Speeds (Excluding May 2020) ---")
    print(top_wind[['datetime', 'latitude', 'longitude', 'wind_speed_kts', 'wave_height_m', 'air_pressure_hpa']].to_string(index=False))
    
    # 3. Extreme Steepness (The "Wall of Water" effect)
    top_steep = df.nlargest(5, 'steepness')
    print("\n--- 3. Extreme Wave Steepness ---")
    print(top_steep[['datetime', 'latitude', 'longitude', 'wave_height_m', 'wave_period_s', 'steepness', 'wind_speed_kts']].to_string(index=False))

if __name__ == "__main__":
    run()
