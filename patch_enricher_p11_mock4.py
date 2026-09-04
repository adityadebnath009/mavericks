import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Add @classmethod back to enrich_feature_collection
content = content.replace("    def enrich_feature_collection", "    @classmethod\n    def enrich_feature_collection")

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

