import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Remove duplicate classmethods anywhere they occur in a row
content = re.sub(r'(?:\s*@classmethod)+\s*@classmethod', '\n    @classmethod', content)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

