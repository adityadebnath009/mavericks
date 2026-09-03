import re

with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

old_block = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    global _pfz_cache, _pfz_cache_time
    import time
    now = time.time()
    if _pfz_cache and (now - _pfz_cache_time) < 3600:
        return _pfz_cache
    try:
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        _pfz_cache = PFZEnricherService.enrich_feature_collection(raw_geojson)
        _pfz_cache_time = now
        return _pfz_cache
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enrich PFZ lines: {str(e)}")"""

new_block = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    cached_collection = PFZEnricherService.get_cached_pfz_collection()
    if cached_collection:
        return cached_collection
    try:
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        return PFZEnricherService.enrich_feature_collection(raw_geojson)
    except Exception as e:
        return PFZEnricherService.get_raw_pfz_with_fallback()"""

content = content.replace(old_block, new_block)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(content)

