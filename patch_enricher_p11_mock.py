import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Add get_cached_pfz_collection and allow cycle kwarg
mock_code = """
    @classmethod
    def get_cached_pfz_collection(cls):
        return None

    @classmethod
    def get_raw_pfz_with_fallback(cls):
        from app.core.exceptions import DataUnavailableError
        return {"type": "FeatureCollection", "enrichment_status": "PARTIAL_RAW_FALLBACK", "features": []}

"""

# find enrich_feature_collection and add cycle=None
content = content.replace("def enrich_feature_collection(cls, geojson_data: dict) -> dict:", "def enrich_feature_collection(cls, geojson_data: dict, cycle=None) -> dict:")

# insert the mock methods
content = content.replace("    def enrich_feature_collection", mock_code + "    def enrich_feature_collection")

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)

