import xarray as xr
ds = xr.open_dataset("https://incois.gov.in/dods/ww3_d1", engine="pydap")
print("WW3 Lats:", ds.lat.values[:5])
print("WW3 Lons:", ds.lon.values[:5])
ds_c = xr.open_dataset("https://incois.gov.in/dods/currents_d1", engine="pydap")
print("Curr Lats:", ds_c.LAT.values[:5])
print("Curr Lons:", ds_c.LON.values[:5])
