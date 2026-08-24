import io
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Constants
MS_TO_KNOTS = 1.943844492

# Standard columns expected in files
WEATHER_COLS = ['YYYYMMDD', 'HHMM', 'UWND', 'VWND', 'WSPD', 'WDIR', 'AIRT', 'SST', 'RH', 'SDATH1', 'SDATH2']
PRESSURE_COLS = ['YYYYMMDD', 'HHMM', 'SLP', 'Q', 'S']

def parse_pmel_file(filepath: Path, expected_cols: list) -> pd.DataFrame:
    """Read a PMEL ASCII file, filtering out metadata headers and inner block dividers."""
    print(f"Parsing file: {filepath.name}")
    data_lines = []
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()
            # Skip empty lines
            if not stripped:
                continue
            # Data rows always start with a date (YYYYMMDD), which is a digit
            if stripped[0].isdigit():
                # Split by space and ensure we match expected number of fields
                parts = stripped.split()
                if len(parts) >= len(expected_cols):
                    # Keep only the columns we expect
                    data_lines.append(' '.join(parts[:len(expected_cols)]))
                else:
                    # Pad if there are fewer columns than expected
                    padded = parts + [np.nan] * (len(expected_cols) - len(parts))
                    data_lines.append(' '.join(map(str, padded)))
                    
    # Parse the space-separated clean data lines
    df = pd.read_csv(
        io.StringIO('\n'.join(data_lines)),
        sep=r'\s+',
        header=None,
        names=expected_cols,
        dtype={expected_cols[0]: str, expected_cols[1]: str}
    )
    
    # Parse timestamp
    df['datetime'] = pd.to_datetime(df[expected_cols[0]] + ' ' + df[expected_cols[1]], format='%Y%m%d %H%M')
    return df

def load_pmel_weather(filepath: Path) -> pd.DataFrame:
    """Load, clean, and convert weather parameters."""
    df = parse_pmel_file(filepath, WEATHER_COLS)
    
    # Convert and clean numeric columns
    cols_to_clean = ['UWND', 'VWND', 'WSPD', 'WDIR', 'AIRT', 'SST', 'RH']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # PMEL missing value indicator is -99.9 or -99.90
            df.loc[df[col] == -99.9, col] = np.nan
            
    # Rename columns to match ORCA conventions
    df = df.rename(columns={
        'WSPD': 'wind_speed_ms',
        'WDIR': 'wind_direction_deg',
        'AIRT': 'air_temperature_c',
        'SST': 'water_temperature_c',
        'RH': 'relative_humidity_pct'
    })
    
    # Convert wind speed to knots
    if 'wind_speed_ms' in df.columns:
        df['wind_speed_kts'] = df['wind_speed_ms'] * MS_TO_KNOTS
        
    return df[['datetime', 'wind_speed_kts', 'wind_direction_deg', 'air_temperature_c', 'water_temperature_c', 'relative_humidity_pct']]

def load_pmel_pressure(filepath: Path) -> pd.DataFrame:
    """Load and clean Sea Level Pressure."""
    df = parse_pmel_file(filepath, PRESSURE_COLS)
    
    # Convert and clean numeric column
    if 'SLP' in df.columns:
        df['SLP'] = pd.to_numeric(df['SLP'], errors='coerce')
        # PMEL missing value indicator is -9.9 or -9.90
        df.loc[df['SLP'] <= -9.0, 'SLP'] = np.nan
        df = df.rename(columns={'SLP': 'air_pressure_hpa'})
        
    return df[['datetime', 'air_pressure_hpa']]

def assign_proxy_risk(row: pd.Series) -> int:
    """Assign risk class (0=LOW, 1=MODERATE, 2=HIGH, 3=EXTREME) based on storm proxies."""
    severity = 0
    wind = row.get('wind_speed_kts')
    pressure = row.get('air_pressure_hpa')

    # Wind speed thresholds (knots)
    if pd.notna(wind):
        if wind >= 34.0:    # Gale force winds
            severity = max(severity, 3)
        elif wind >= 28.0:  # Very rough sea conditions
            severity = max(severity, 2)
        elif wind >= 18.0:  # Small craft warning threshold
            severity = max(severity, 1)

    # Air pressure drops (depression/cyclone indicators)
    if pd.notna(pressure):
        if pressure < 990.0:    # Deep Depression / Cyclone
            severity = max(severity, 3)
        elif pressure < 1000.0:  # Depression
            severity = max(severity, 2)
        elif pressure < 1008.0:  # Low Pressure System
            severity = max(severity, 1)

    return severity

def process_station(station_name: str, weather_file: Path, pressure_file: Path = None) -> pd.DataFrame:
    """Process, clean, merge, and label data for a single buoy station."""
    print(f"\n--- Processing Station: {station_name} ---")
    
    weather_df = load_pmel_weather(weather_file)
    
    if pressure_file and pressure_file.exists():
        pressure_df = load_pmel_pressure(pressure_file)
        merged = pd.merge(weather_df, pressure_df, on='datetime', how='inner')
    else:
        print("Note: No pressure file provided or found. Filling pressure with NaN.")
        merged = weather_df.copy()
        merged['air_pressure_hpa'] = np.nan
        
    merged['station_name'] = station_name
    
    # Add coordinates based on buoy site
    if 'bay_of_bengal_15n90e' in station_name:
        merged['latitude'] = 15.0
        merged['longitude'] = 90.0
    elif 'bay_of_bengal_12n90e' in station_name:
        merged['latitude'] = 12.0
        merged['longitude'] = 90.0
    elif 'bay_of_bengal_8n90e' in station_name:
        merged['latitude'] = 8.0
        merged['longitude'] = 90.0
    elif 'arabian_sea_15n65e' in station_name:
        merged['latitude'] = 15.0
        merged['longitude'] = 65.0
    elif 'arabian_sea_8n67e' in station_name:
        merged['latitude'] = 8.0
        merged['longitude'] = 67.0
    elif 'arabian_sea_4n67e' in station_name:
        merged['latitude'] = 4.0
        merged['longitude'] = 67.0
    else:
        merged['latitude'] = np.nan
        merged['longitude'] = np.nan
        
    # Drop records where all important weather readings are missing
    merged = merged.dropna(subset=['wind_speed_kts', 'air_pressure_hpa'], how='all')
    
    # Calculate proxy risk labels
    merged['risk_class'] = merged.apply(assign_proxy_risk, axis=1)
    
    risk_labels = {0: 'LOW', 1: 'MODERATE', 2: 'HIGH', 3: 'EXTREME'}
    merged['risk_label'] = merged['risk_class'].map(risk_labels)
    
    print(f"Station {station_name} processed. Rows: {len(merged):,}")
    return merged

def main():
    # Ensure processed directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define stations config
    stations_config = [
        {
            "name": "bay_of_bengal_15n90e",
            "weather": RAW_DIR / "bay_of_bengal_weather.ascii",
            "pressure": RAW_DIR / "bay_of_bengal_pressure.ascii"
        },
        {
            "name": "bay_of_bengal_12n90e",
            "weather": RAW_DIR / "bay_of_bengal_2_weather.ascii",
            "pressure": None
        },
        {
            "name": "bay_of_bengal_8n90e",
            "weather": RAW_DIR / "bay_of_bengal_3_weather.ascii",
            "pressure": None
        },
        {
            "name": "arabian_sea_15n65e",
            "weather": RAW_DIR / "arabian_sea_weather.ascii",
            "pressure": RAW_DIR / "arabian_sea_pressure.ascii"
        },
        {
            "name": "arabian_sea_8n67e",
            "weather": RAW_DIR / "arabian_sea_2_weather.ascii",
            "pressure": None
        },
        {
            "name": "arabian_sea_4n67e",
            "weather": RAW_DIR / "arabian_sea_3_weather.ascii",
            "pressure": None
        }
    ]
    
    records = []
    
    for station in stations_config:
        w_file = station["weather"]
        p_file = station["pressure"]
        
        if w_file.exists():
            station_df = process_station(station["name"], w_file, p_file)
            records.append(station_df)
        else:
            print(f"Warning: Weather file not found for station {station['name']} at {w_file}")
            
    if not records:
        print("Error: No data files processed!")
        return
        
    # Combine all datasets
    combined_df = pd.concat(records, ignore_index=True)
    
    # Sort chronologically
    combined_df = combined_df.sort_values(by=['station_name', 'datetime'])
    
    # Save datasets
    csv_out = PROCESSED_DIR / "marine_risk_processed.csv"
    combined_df.to_csv(csv_out, index=False)
    
    print("\n" + "="*50)
    print("PREPROCESSING COMPLETE")
    print("="*50)
    print(f"Combined dataset saved to: {csv_out}")
    print(f"Total Rows: {len(combined_df):,}")
    print("\nRisk Class Distribution:")
    print(combined_df['risk_label'].value_counts())
    print("\nRows per station:")
    print(combined_df['station_name'].value_counts())

if __name__ == "__main__":
    main()
