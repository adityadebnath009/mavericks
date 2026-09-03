import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Add a check for enrichment success
find_str = """        payload = {
            "type": "FeatureCollection",
            "features": enriched_features,
            "cache_version": 1,
            "pfz_cycle": cycle,
            "enrichment_status": "READY",
            "generated_at": iso_timestamp,
            "source": "INCOIS GeoServer + OPeNDAP"
        }
        
        cls._atomic_write_json(ENRICHMENT_CACHE_FILE, payload)"""

replace_str = """        # If no points were enriched with metrics, consider it a partial/failed run
        has_metrics = any(f["properties"].get("sst_median") is not None for f in enriched_features)
        
        status = "READY" if has_metrics else "PARTIAL_RAW_FALLBACK"
        
        payload = {
            "type": "FeatureCollection",
            "features": enriched_features,
            "cache_version": 1,
            "pfz_cycle": cycle,
            "enrichment_status": status,
            "generated_at": iso_timestamp,
            "source": "INCOIS GeoServer + OPeNDAP"
        }
        
        # Only overwrite the cache if we have a successful READY run,
        # OR if there is no cache at all. Do not overwrite a good READY cache with a PARTIAL one.
        if status == "READY":
            cls._atomic_write_json(ENRICHMENT_CACHE_FILE, payload)
        elif not os.path.exists(ENRICHMENT_CACHE_FILE):
            cls._atomic_write_json(ENRICHMENT_CACHE_FILE, payload)"""

if find_str in content:
    content = content.replace(find_str, replace_str)
else:
    print("Could not find string to replace")

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
