import xarray as xr
from datetime import datetime, timedelta

def get_url(base):
    import urllib.request
    for lag in [0, 1, 2, 3]:
        d = (datetime.utcnow() - timedelta(days=lag)).strftime("%Y%m%d")
        url = base.format(d)
        try:
            urllib.request.urlopen(url + ".dds", timeout=2)
            return url
        except:
            pass
    return None

ww3_url = get_url("https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_{}.nc")
if ww3_url:
    ds = xr.open_dataset(ww3_url, engine="netcdf4")
    print("WW3 Dims:", ds.dims)
    print("WW3 Vars:", list(ds.data_vars.keys()))

curr_url = get_url("https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_{}.nc")
if curr_url:
    ds = xr.open_dataset(curr_url, engine="netcdf4")
    print("Curr Dims:", ds.dims)
    print("Curr Vars:", list(ds.data_vars.keys()))
