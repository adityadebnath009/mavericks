import re
with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

# Add dependencies to the top
content = content.replace("from fastapi import APIRouter, Query, HTTPException", "from fastapi import APIRouter, Query, HTTPException, Depends\nfrom sqlalchemy.orm import Session\nfrom app.db.session import get_db\nfrom app.db.models import PFZAdvisory")

old_pfz = """_pfz_cache = None
_pfz_cache_time = 0

@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines():
    \"\"\"
    Proxies the WFS GeoJSON request to retrieve dynamic PFZ lines,
    enriched with multi-point environmental medians (SST, CHL, Wave, Current, Wind)
    and zero static species inference.
    \"\"\"
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

new_pfz = """@router.get("/pfz-lines")
@router.get("/pfz-lines/")
def get_pfz_advisory_lines(db: Session = Depends(get_db)):
    \"\"\"
    Serves the most recent active PFZ advisory lines directly from the database.
    This eliminates network polling stalls. The database is updated via a background cron worker.
    \"\"\"
    try:
        active = db.query(PFZAdvisory).filter(PFZAdvisory.status == "active").first()
        if active and active.content_json:
            return active.content_json
        
        # Fallback if DB is empty
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        return PFZEnricherService.enrich_feature_collection(raw_geojson)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch PFZ lines: {str(e)}")"""

content = content.replace(old_pfz, new_pfz)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(content)
