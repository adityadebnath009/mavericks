import re
with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

content = content.replace("ww3_url = IncoisDatasetResolver.WW3_URL", "ww3_url = IncoisDatasetResolver.get_ww3_url()")

with open("backend/app/api/endpoints/safety.py", "w") as f:
    f.write(content)
