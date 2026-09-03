import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

old_return = """        return {
            "type": "FeatureCollection",
            "features": enriched_features,
            "enriched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }"""

new_return = """        res = {
            "type": "FeatureCollection",
            "features": enriched_features,
            "enriched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "enrichment_status": "READY"
        }
        if cycle: res["pfz_cycle"] = cycle
        return res"""

content = content.replace(old_return, new_return)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

