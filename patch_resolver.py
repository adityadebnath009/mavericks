with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Replace WW3 url
content = content.replace(
    'return "https://incois.gov.in/thredds/catalog/OOS/INCOIS_WW3/catalog.xml"',
    'return "https://incois.gov.in/thredds/catalog/osf/ww3/catalog.xml"'
)

# Wait, let's also make _get_latest_catalog_dataset use verify=False
content = content.replace(
    'response = requests.get(catalog_url, timeout=10)',
    'response = requests.get(catalog_url, timeout=10, verify=False)'
)

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
