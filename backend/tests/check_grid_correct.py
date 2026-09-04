from app.api.services.incois_resolver import IncoisDatasetResolver
import xarray as xr

url = IncoisDatasetResolver.get_ww3_url()
ds = xr.open_dataset(url, engine="pydap")
lats = ds.lat.values[:5]
lons = ds.lon.values[:5]
print("Lats:", lats)
print("Lons:", lons)
print("Lat spacing:", lats[1] - lats[0])
print("Lon spacing:", lons[1] - lons[0])
