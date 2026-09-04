import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Add enrichment_status and pfz_cycle to the returned dict of enrich_feature_collection
mock_injection = """
        if cycle: geojson_data["pfz_cycle"] = cycle
        geojson_data["enrichment_status"] = "READY"
        return geojson_data
"""

# Replace the end of enrich_feature_collection
content = content.replace("        return geojson_data", mock_injection)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

