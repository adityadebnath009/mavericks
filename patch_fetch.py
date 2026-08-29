import re
with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

old_fetch = """            # Using dynamic real-time URLs with OPeNDAP-capable netcdf4 engine
            ds_ww3 = xr.open_dataset(cls.get_ww3_url(), engine="pydap")
            ds_curr = xr.open_dataset(cls.get_currents_url(), engine="pydap")"""

new_fetch = """            # Using dynamic real-time URLs with OPeNDAP-capable pydap engine
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ds_ww3 = xr.open_dataset(cls.get_ww3_url().replace('https://', 'http://'), engine="pydap")
                ds_curr = xr.open_dataset(cls.get_currents_url().replace('https://', 'http://'), engine="pydap")"""
content = content.replace(old_fetch, new_fetch)

old_grid = """            ds_ww3 = xr.open_dataset(cls.get_ww3_url(), engine="pydap")
            ds_curr = xr.open_dataset(cls.get_currents_url(), engine="pydap")"""

new_grid = """            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ds_ww3 = xr.open_dataset(cls.get_ww3_url().replace('https://', 'http://'), engine="pydap")
                ds_curr = xr.open_dataset(cls.get_currents_url().replace('https://', 'http://'), engine="pydap")"""
content = content.replace(old_grid, new_grid)

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
