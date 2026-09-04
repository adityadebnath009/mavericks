import pandas as pd

def run():
    df = pd.read_csv('/Users/adityadebnath/Downloads/indian_coastal_marine_dataset_2020_2025 (2).csv')
    
    print("--- 1. Data Types and Sample ---")
    print(df.dtypes.head(15))
    print(df[['datetime', 'latitude', 'longitude', 'wave_height_m', 'wave_period_s', 'wind_speed_kts']].head(5))
    
    print("\n--- 2. Extreme Wave Height Records ---")
    top_5 = df.nlargest(5, 'wave_height_m')
    print(top_5[['datetime', 'latitude', 'longitude', 'wave_height_m', 'wave_period_s', 'wind_speed_kts', 'air_pressure_hpa']])
    
    print("\n--- 3. Distribution Metrics for Context ---")
    print(df[['wave_height_m', 'wave_period_s', 'wind_speed_kts']].describe(percentiles=[.5, .9, .95, .99]))

if __name__ == "__main__":
    run()
