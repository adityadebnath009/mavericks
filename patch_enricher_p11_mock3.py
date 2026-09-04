import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

mock_code = """
    @classmethod
    def get_cached_pfz_collection(cls):
        import os, json
        # CACHE_DIR is at the top of pfz_enricher.py
        cache_file = os.path.join(CACHE_DIR, "_pfz_cache.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None
"""

# Replace the current get_cached_pfz_collection
start = content.find("    @classmethod\n    def get_cached_pfz_collection(cls):")
end = content.find("    @classmethod\n    def get_raw_pfz_with_fallback(cls):")
if start != -1 and end != -1:
    content = content[:start] + mock_code + content[end:]

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

