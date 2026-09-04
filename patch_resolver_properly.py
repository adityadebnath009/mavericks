with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Correctly replace WW3 url
content = content.replace(
    'url = "https://incois.gov.in/thredds/catalog/OOS/INCOIS_WW3/catalog.xml"',
    'url = "https://incois.gov.in/thredds/catalog/osf/ww3/catalog.xml"'
)

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
