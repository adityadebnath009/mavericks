import xarray as xr
import numpy as np
import pandas as pd
import time
import math

def test_grid_performance():
    print("Connecting to INCOIS OPENDAP WW3 dataset...")
    t_start = time.time()
    
    ww3_url = "https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_20260825.nc"
    ds = xr.open_dataset(ww3_url)
    
    # Target timestamp: Day 1, Hour 12
    target_time = pd.to_datetime("2026-08-26 12:00:00")
    lookback_time = target_time - pd.DateOffset(hours=6)
    
    print(f"Slicing 2D grid for time: {target_time} (lookback: {lookback_time})...")
    
    # Slicing with step size of 4 (every 4th grid point = 0.4 degree spacing, yielding ~50x75=3750 cells)
    grid_slice = ds.sel(
        IOYAXIS=slice(5.0, 25.0),
        IOXAXIS=slice(65.0, 95.0)
    ).isel(
        IOYAXIS=slice(None, None, 4),
        IOXAXIS=slice(None, None, 4)
    ).sel(
        TIME=[lookback_time, target_time],
        method="nearest"
    )
    
    print(f"Slicing configuration set. Now loading variables...")
    t_load = time.time()
    
    hsea_initial = grid_slice.PHS00.isel(TIME=0).values
    hsea_final = grid_slice.PHS00.isel(TIME=1).values
    
    hs = grid_slice.HS.isel(TIME=1).values
    stp = grid_slice.STP.isel(TIME=1).values
    spr_raw = grid_slice.SPR.isel(TIME=1).values
    
    print(f"Data download completed in {time.time() - t_load:.2f} seconds.")
    
    # Vectorized BSI calculations
    # 1. Steepness Index: (Stp / 0.05) * (Hs / 2.5)
    I_steepness = (stp / 0.05) * (hs / 2.5)
    S_steepness = np.where(I_steepness >= 0.8, 1, 0)
    
    # 2. Crossing Sea Index: 0.5 * Hs * exp(-10 * (s_s - 1.0)^2)
    spr_rad = np.radians(spr_raw)
    s_s = np.sqrt(2.0 * (1.0 - np.cos(spr_rad)))
    I_crossing = 0.5 * hs * np.exp(-10.0 * (s_s - 1.0)**2)
    S_crossing = np.where(I_crossing >= 0.65, 2, 0)
    
    # 3. Rapid Development: |Hsea_f - Hsea_i| / Hsea_i
    Z_6h = np.where(hsea_initial > 0.0, np.abs(hsea_final - hsea_initial) / hsea_initial, 0.0)
    S_rapiddev = np.where(Z_6h >= 0.2, 4, 0)
    
    # Final BSI grid
    bsi = S_steepness + S_crossing + S_rapiddev
    
    print(f"Calculations completed in {time.time() - t_start:.2f} seconds.")
    print("BSI Grid shape:", bsi.shape)
    print("Non-zero BSI counts:", np.sum(bsi > 0))

if __name__ == "__main__":
    test_grid_performance()
