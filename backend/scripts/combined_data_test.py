import xarray as xr
import numpy as np
import pandas as pd
import math
import json
import os

def run_test():
    lat = 15.0
    lon = 73.0
    # Target time in WW3 timeline
    target_time_str = "2026-08-26T12:00:00"
    target_time = pd.to_datetime(target_time_str)

    print(f"Connecting to INCOIS THREDDS via OPENDAP...")
    print(f"Target location: Lat {lat}, Lon {lon}")
    print(f"Target time: {target_time_str}")

    # 1. Load WW3 dataset remotely
    ww3_url = "https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_20260825.nc"
    ww3 = xr.open_dataset(ww3_url)

    # 2. Load Currents dataset remotely
    curr_url = "https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_20260824.nc"
    curr = xr.open_dataset(curr_url)

    # 3. Spatial & Temporal subsetting for WW3
    # WW3 coordinates: IOYAXIS (lat), IOXAXIS (lon), TIME
    ww3_slice = ww3.sel(
        IOYAXIS=lat,
        IOXAXIS=lon,
        TIME=target_time,
        method="nearest"
    )

    # 4. Spatial & Temporal subsetting for Currents
    # Currents coordinates: LAT, LON, TAXIS, DEPTH1_1=0
    curr_slice = curr.sel(
        LAT=lat,
        LON=lon,
        TAXIS=target_time,
        DEPTH1_1=0.0,
        method="nearest"
    )

    # Extract values
    hs = float(ww3_slice.HS.values)
    steepness = float(ww3_slice.STP.values)
    dir_spread = float(ww3_slice.SPR.values)
    wave_dir = float(ww3_slice.MWD.values)
    period = float(ww3_slice.T02.values)
    
    u_curr = float(curr_slice.U.values)
    v_curr = float(curr_slice.V.values)
    
    # Derive Current Speed: speed = sqrt(U^2 + V^2)
    curr_speed = math.sqrt(u_curr**2 + v_curr**2)
    
    # Derive Current Direction (oceanographic convention: direction towards which current flows)
    curr_dir_rad = math.atan2(u_curr, v_curr)
    curr_dir_deg = math.degrees(curr_dir_rad)
    curr_dir = curr_dir_deg if curr_dir_deg >= 0 else 360.0 + curr_dir_deg

    record = {
        "latitude": lat,
        "longitude": lon,
        "ww3_timestamp": str(ww3_slice.TIME.values),
        "currents_timestamp": str(curr_slice.TAXIS.values),
        "time_offset_hours": float((pd.to_datetime(ww3_slice.TIME.values) - pd.to_datetime(curr_slice.TAXIS.values)).total_seconds() / 3600.0),
        "ww3": {
            "significant_wave_height_m": hs,
            "wave_steepness": steepness,
            "directional_spread": dir_spread,
            "mean_wave_direction_deg": wave_dir,
            "mean_period_tz_sec": period
        },
        "currents": {
            "u_component_m_s": u_curr,
            "v_component_m_s": v_curr,
            "derived_current_speed_m_s": curr_speed,
            "derived_current_direction_deg": curr_dir
        }
    }

    print("\n--- COMBINED RECORD ---")
    print(json.dumps(record, indent=2))

    # Save to artifacts directory
    artifact_dir = "/Users/adityadebnath/.gemini/antigravity/brain/c4540e39-f7a2-419d-8973-96e839de10e7"
    out_file = os.path.join(artifact_dir, "combined_record_test.json")
    with open(out_file, "w") as f:
        json.dump(record, f, indent=2)
    print(f"\nSaved combined test record to: {out_file}")

if __name__ == "__main__":
    run_test()
