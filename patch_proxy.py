import re

with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

# Fix the WMS proxy to disable SSL verification and increase timeout
new_content = content.replace(
    'res = requests.get(incois_url, params=params, timeout=10)',
    'res = requests.get(incois_url, params=params, timeout=30, verify=False)'
)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(new_content)
