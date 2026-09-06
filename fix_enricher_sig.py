import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

old_sig = "def enrich_feature_collection(cls, geojson_data: dict, cycle=None) -> dict:"
new_sig = "def enrich_feature_collection(cls, geojson_data: dict, cycle=None, **kwargs) -> dict:"
content = content.replace(old_sig, new_sig)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
