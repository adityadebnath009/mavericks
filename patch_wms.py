import re
with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

content = content.replace(
    "'https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms?service=WMS&request=GetMap&layers=PFZ-TUNA-SST-CHL:sst&styles=&format=image/png&transparent=true&version=1.1.1&width=256&height=256&srs=EPSG:3857&bbox={bbox-epsg-3857}'",
    "getApiUrl('/api/incois/wms/proxy?layers=PFZ-TUNA-SST-CHL:sst&bbox={bbox-epsg-3857}')"
)

content = content.replace(
    "'https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms?service=WMS&request=GetMap&layers=PFZ-TUNA-SST-CHL:chl&styles=&format=image/png&transparent=true&version=1.1.1&width=256&height=256&srs=EPSG:3857&bbox={bbox-epsg-3857}'",
    "getApiUrl('/api/incois/wms/proxy?layers=PFZ-TUNA-SST-CHL:chl&bbox={bbox-epsg-3857}')"
)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
