import re
with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

content = content.replace('engine="netcdf4"', 'engine="pydap"')

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
