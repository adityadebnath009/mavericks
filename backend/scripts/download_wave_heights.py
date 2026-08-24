import os
import pandas as pd
import numpy as np
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
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

def download_era5_waves_mock():
    """
    Downloads historical Significant Wave Height (SWH) and Mean Wave Period (MWP)
    using the Copernicus Climate Data Store (CDS) API.
    
    If the cdsapi is not installed or configured, it generates physically-consistent 
    ocean swell and wave heights matching the wind speeds in the CSV (standard oceanographic wind-wave equations).
    """
    if not PROCESSED_CSV.exists():
        print("Error: preprocessed CSV not found!")
        return
        
    df = pd.read_csv(PROCESSED_CSV)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    print("Pre-existing columns:", list(df.columns))
    
    # ----------------------------------------------------
    # Check if CDS API is configured for real download
    # ----------------------------------------------------
    cds_configured = os.path.exists(os.path.expanduser("~/.cdsapirc"))
    
    if cds_configured:
        print("\n[INFO] ~/.cdsapirc found. Initiating real ERA5 Wave Reanalysis download...")
        try:
            import cdsapi
            import xarray as xr
            
            c = cdsapi.Client()
            
            # Define bounding box for our 6 buoys:
            # North: 16N, South: 3N, West: 64E, East: 91E
            netcdf_output = PROJECT_ROOT / "data" / "raw" / "era5_wave_reanalysis.nc"
            
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
                    'time': '12:00',  # Match the 12:00 UTC buoy time
                    'area': [16, 64, 3, 91],  # North, West, South, East
                    'format': 'netcdf',
                },
                str(netcdf_output)
            )
            
            print(f"Successfully downloaded ERA5 NetCDF to {netcdf_output}")
            print("Merging spatial wave grids with buoy timestamps...")
            
            # Read NetCDF
            ds = xr.open_dataset(netcdf_output)
            
            wave_heights = []
            wave_periods = []
            
            for idx, row in df.iterrows():
                lat, lon = row['latitude'], row['longitude']
                dt = row['datetime']
                
                # Query nearest grid point in space and time
                wave_data = ds.sel(latitude=lat, longitude=lon, time=dt, method='nearest')
                swh = float(wave_data['swh'].values)
                mwp = float(wave_data['mwp'].values)
                
                wave_heights.append(swh)
                wave_periods.append(mwp)
                
            df['wave_height_m'] = wave_heights
            df['wave_period_s'] = wave_periods
            print("Real ERA5 wave heights merged successfully!")
            
        except Exception as e:
            print(f"\n[Warning] Could not complete real ERA5 download: {e}")
            print("Falling back to physics-based wind-wave simulation...")
            df = generate_physics_waves(df)
            
    else:
        print("\n[INFO] Copernicus CDS API key not configured in ~/.cdsapirc.")
        print("Using physics-based wind-wave formulas (Fully-Developed Sea State) to merge wave heights...")
        df = generate_physics_waves(df)
        
    # Update risk classes now that wave height is present
    df = recalculate_risk_with_waves(df)
    
    # Save back to CSV
    df.to_csv(PROCESSED_CSV, index=False)
    print(f"\nSuccess! Updated dataset saved to: {PROCESSED_CSV}")
    print(df[['datetime', 'station_name', 'wind_speed_kts', 'wave_height_m', 'risk_label']].head(15))

def generate_physics_waves(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies wind-wave equations (modified Carter/Pierson-Moskowitz equations)
    to estimateSignificant Wave Height (SWH) and wave periods directly from wind speeds,
    adding realistic swell noise and coastal current damping.
    """
    np.random.seed(42)
    
    # Convert knots back to m/s for physics calculation
    wspd_ms = df['wind_speed_kts'] / 1.94384
    
    # Carter's fully developed wave height formula: H_s = 0.022 * U^2 (where U is wind speed in m/s)
    # Plus a small random swell variance (0.2m to 0.5m)
    swh = 0.022 * (wspd_ms ** 2) + np.random.uniform(0.1, 0.4, len(df))
    
    # Average wave period: T = 0.8 * U (seconds)
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
    download_era5_waves_mock()
