import re
with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Fix _fetch_remote slicing
content = content.replace('ds_ww3.sel(IOYAXIS=lat, IOXAXIS=lon, method="nearest")',
                          'ds_ww3.sel(lat=lat, lon=lon, method="nearest")')

# Fix resolve_vector_grid slicing
content = content.replace('ww3_slice = ds_ww3.sel(IOYAXIS=slice(5, 25), IOXAXIS=slice(65, 95)).isel(TIME=time_idx).coarsen(IOYAXIS=2, IOXAXIS=2, boundary="trim").mean()',
                          'ww3_slice = ds_ww3.sel(lat=slice(5, 25), lon=slice(65, 95)).isel(TIME=time_idx).coarsen(lat=2, lon=2, boundary="trim").mean()')

# Fix resolve_vector_grid values access
content = content.replace('ww3_slice.IOYAXIS.values.ravel()', 'ww3_slice.lat.values.ravel()')
content = content.replace('ww3_slice.IOXAXIS.values.ravel()', 'ww3_slice.lon.values.ravel()')

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
