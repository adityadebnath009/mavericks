import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

mock_code = """
    @classmethod
    def get_cached_pfz_collection(cls):
        import os, json
        cache_file = os.path.join(CACHE_DIR, "pfz_enriched.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        return None
"""

content = re.sub(r'    @classmethod\n    def get_cached_pfz_collection\(cls\):\n        return None', mock_code, content)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

