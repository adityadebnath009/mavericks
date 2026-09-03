import re

with open("backend/app/api/services/cache_warmer.py", "r") as f:
    content = f.read()

find_str = """            # P1.1: Delegate heavy enrichment to the parallelized background service
            PFZEnricherService.enrich_feature_collection(pfz_features, cycle=current_cycle)
        except Exception as e:"""

replace_str = """            # P1.1: Delegate heavy enrichment to the parallelized background service
            res = PFZEnricherService.enrich_feature_collection(pfz_features, cycle=current_cycle)
            if res.get("enrichment_status") == "PARTIAL_RAW_FALLBACK":
                raise Exception("PFZ telemetry enrichment timed out or failed; raw geometry preserved.")
        except Exception as e:"""

if find_str in content:
    content = content.replace(find_str, replace_str)
else:
    print("String not found")

with open("backend/app/api/services/cache_warmer.py", "w") as f:
    f.write(content)

