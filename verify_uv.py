import xarray as xr
import numpy as np
from datetime import datetime, timedelta

def get_url(base):
    import urllib.request
    for lag in [0, 1, 2, 3]:
        dstr = (datetime.utcnow() - timedelta(days=lag)).strftime("%Y%m%d")
        url = base.format(dstr)
        try:
            urllib.request.urlopen(url + ".dds", timeout=2)
            return url
        except:
            pass
    return None

print("--- Validating INCOIS U/V Data ---")
ww3_url = get_url("https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_{}.nc")
if ww3_url:
    print(f"Opening WW3: {ww3_url}")
    ds = xr.open_dataset(ww3_url, engine="netcdf4")
    # Take a tiny slice in Arabian Sea (lat 10-12, lon 70-72)
    sl = ds.sel(IOYAXIS=slice(10, 12), IOXAXIS=slice(70, 72))
    u = sl.UWND.isel(TIME=0).values
    v = sl.VWND.isel(TIME=0).values
    print("WW3 U (first row):", u[0][:5])
    print("WW3 V (first row):", v[0][:5])
    print(f"Valid points count: {np.count_nonzero(~np.isnan(u))}")

curr_url = get_url("https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_{}.nc")
if curr_url:
    print(f"Opening Currents: {curr_url}")
    ds = xr.open_dataset(curr_url, engine="netcdf4")
    # Currents grid uses LAT and LON
    sl = ds.sel(LAT=slice(10, 12), LON=slice(70, 72))
    u = sl.U.isel(TAXIS=0, DEPTH1_1=0).values
    v = sl.V.isel(TAXIS=0, DEPTH1_1=0).values
    print("Currents U (first row):", u[0][:5])
    print("Currents V (first row):", v[0][:5])
    print(f"Valid points count: {np.count_nonzero(~np.isnan(u))}")

