import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

content = content.replace('_pfz_cache.json', 'pfz_enrichment_cache.json')

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

