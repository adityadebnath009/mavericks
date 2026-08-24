import os
import io
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "marine_risk_processed.csv"

# Coordinates of our 6 buoys
BUOY_COORDINATES = {
    "bay_of_bengal_15n90e": (15.0, 90.0),
    "bay_of_bengal_12n90e": (12.0, 90.0),
    "bay_of_bengal_8n90e": (8.0, 90.0),
    "arabian_sea_15n65e": (15.0, 65.0),
    "arabian_sea_8n67e": (8.0, 67.0),
    "arabian_sea_4n67e": (4.0, 67.0)
}

def download_era5_waves():
    """
    Integrates Significant Wave Height (SWH) and Mean Wave Period (MWP) into our buoy dataset.
    Prioritizes reading the local 'data/raw/era5_wave_reanalysis.nc' NetCDF file.
    If not present, attempts to fetch it via cdsapi. If config is missing, falls back
    to physics-based wind-wave equations.
    """
    if not PROCESSED_CSV.exists():
        print("Error: preprocessed CSV not found!")
        return
        
    df = pd.read_csv(PROCESSED_CSV)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    netcdf_output = RAW_DIR / "era5_wave_reanalysis.nc"
    
    # ----------------------------------------------------
    # Case 1: NetCDF File is already present in raw/
    # ----------------------------------------------------
    if netcdf_output.exists():
        print(f"\n[INFO] Local NetCDF file found at: {netcdf_output.name}")
        print("Extracting wave parameters from NetCDF grids...")
        try:
            import xarray as xr
            
            # Open the dataset
            ds = xr.open_dataset(netcdf_output)
            
            # Map variable names (ERA5 uses swh/mwp or significant_height_of_combined_wind_waves_and_swell)
            var_keys = list(ds.data_vars)
            coord_keys = list(ds.coords)
            
            print("NetCDF variables:", var_keys)
            print("NetCDF coordinates:", coord_keys)
            
            swh_key = next((k for k in var_keys if 'swh' in k or 'significant' in k), None)
            mwp_key = next((k for k in var_keys if 'mwp' in k or 'period' in k), None)
            time_key = next((k for k in coord_keys if 'time' in k), 'time')
            
            if not swh_key:
                raise KeyError(f"Could not find Significant Wave Height column. Available variables: {var_keys}")
                
            wave_heights = []
            wave_periods = []
            
            for idx, row in df.iterrows():
                lat, lon = row['latitude'], row['longitude']
                dt = row['datetime']
                
                # Query nearest coordinates in space and time
                try:
                    query_dict = {
                        'latitude': lat,
                        'longitude': lon,
                        time_key: dt
                    }
                    subset = ds.sel(**query_dict, method='nearest')
                    
                    swh = float(subset[swh_key].values)
                    mwp = float(subset[mwp_key].values) if mwp_key else np.nan
                    
                except Exception as inner_err:
                    print(f"Coordinate query warning at Lat:{lat}, Lon:{lon}, Time:{dt} - {inner_err}")
                    swh = np.nan
                    mwp = np.nan
                    
                wave_heights.append(swh)
                wave_periods.append(mwp)
                
            df['wave_height_m'] = wave_heights
            if mwp_key:
                df['wave_period_s'] = wave_periods
            else:
                df['wave_period_s'] = np.nan
                
            print("Merged NetCDF wave data successfully!")
            
        except Exception as e:
            print(f"\n[Warning] Could not extract NetCDF wave data: {e}")
            print("Falling back to physics-based wind-wave simulation...")
            df = generate_physics_waves(df)
            
    # ----------------------------------------------------
    # Case 2: No local file, check if CDS API is configured
    # ----------------------------------------------------
    elif os.path.exists(os.path.expanduser("~/.cdsapirc")):
        print("\n[INFO] ~/.cdsapirc found. Initiating real ERA5 Wave Reanalysis download...")
        try:
            import cdsapi
            import xarray as xr
            
            c = cdsapi.Client()
            
            c.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'variable': [
                        'significant_height_of_combined_wind_waves_and_swell',
                        'mean_wave_period'
                    ],
                    'year': [str(y) for y in range(2020, 2027)],
                    'month': [f"{m:02d}" for m in range(1, 13)],
                    'day': [f"{d:02d}" for d in range(1, 32)],
                    'time': '12:00',
                    'area': [18, 60, 2, 95],  # Bounding box covering all buoys
                    'format': 'netcdf',
                },
                str(netcdf_output)
            )
            
            print(f"Successfully downloaded ERA5 NetCDF to {netcdf_output.name}")
            
            # Recursive call now that local NetCDF is downloaded
            return download_era5_waves()
            
        except Exception as e:
            print(f"\n[Warning] Could not complete real ERA5 download: {e}")
            print("Falling back to physics-based wind-wave simulation...")
            df = generate_physics_waves(df)
            
    # ----------------------------------------------------
    # Case 3: No local file and no API key (Fallback)
    # ----------------------------------------------------
    else:
        print("\n[INFO] Local NetCDF not found and Copernicus CDS API key not configured.")
        print("Using physics-based wind-wave formulas (Fully-Developed Sea State) to merge wave heights...")
        df = generate_physics_waves(df)
        
    # Update risk classes now that wave height is present
    df = recalculate_risk_with_waves(df)
    
    # Save back to CSV
    df.to_csv(PROCESSED_CSV, index=False)
    print(f"\nSuccess! Updated dataset saved to: {PROCESSED_CSV}")
    print(df[['datetime', 'station_name', 'wind_speed_kts', 'wave_height_m', 'risk_label']].head(15))

def generate_physics_waves(df: pd.DataFrame) -> pd.DataFrame:
    """Estimates Significant Wave Height (SWH) and periods from wind speed using Carter equations."""
    np.random.seed(42)
    
    # Convert knots back to m/s for physics calculation
    wspd_ms = df['wind_speed_kts'] / 1.94384
    
    # Carter's developed wave height formula: H_s = 0.022 * U^2
    # Plus random swell variance
    swh = 0.022 * (wspd_ms ** 2) + np.random.uniform(0.1, 0.4, len(df))
    
    # Average wave period: T = 0.8 * U
    mwp = 0.8 * wspd_ms + np.random.uniform(2.0, 4.0, len(df))
    
    # Clean up NaNs where wind speed was missing
    swh = np.where(df['wind_speed_kts'].isna(), np.nan, swh)
    mwp = np.where(df['wind_speed_kts'].isna(), np.nan, mwp)
    
    # Clip physically impossible waves
    df['wave_height_m'] = np.clip(swh, 0.2, 12.0)
    df['wave_period_s'] = np.clip(mwp, 2.0, 18.0)
    
    return df

def recalculate_risk_with_waves(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate risk classes now that physical wave heights are merged."""
    
    def assign_risk(row):
        severity = 0
        wind = row.get('wind_speed_kts')
        pressure = row.get('air_pressure_hpa')
        wave = row.get('wave_height_m')
        
        # Wave Height Thresholds (m)
        if pd.notna(wave):
            if wave >= 4.0:
                severity = max(severity, 3)  # EXTREME
            elif wave >= 2.8:
                severity = max(severity, 2)  # HIGH
            elif wave >= 1.5:
                severity = max(severity, 1)  # MODERATE
                
        # Wind Speed Thresholds (knots)
        if pd.notna(wind):
            if wind >= 34.0:
                severity = max(severity, 3)
            elif wind >= 28.0:
                severity = max(severity, 2)
            elif wind >= 18.0:
                severity = max(severity, 1)

        # Pressure Drops (hPa)
        if pd.notna(pressure):
            if pressure < 990.0:
                severity = max(severity, 3)
            elif pressure < 1000.0:
                severity = max(severity, 2)
            elif pressure < 1008.0:
                severity = max(severity, 1)
                
        return severity

    df['risk_class'] = df.apply(assign_risk, axis=1)
    
    risk_labels = {0: 'LOW', 1: 'MODERATE', 2: 'HIGH', 3: 'EXTREME'}
    df['risk_label'] = df['risk_class'].map(risk_labels)
    
    print("\nUpdated Risk Class Distribution with Wave Heights:")
    print(df['risk_label'].value_counts())
    return df

if __name__ == "__main__":
    download_era5_waves()
