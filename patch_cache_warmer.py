import re

with open("backend/app/api/services/cache_warmer.py", "r") as f:
    content = f.read()

if "PFZEnricherService" not in content[:500]:
    content = "from app.api.services.pfz_enricher import PFZEnricherService\n" + content

with open("backend/app/api/services/cache_warmer.py", "w") as f:
    f.write(content)
