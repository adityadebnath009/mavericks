import re

with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

old_func = """@router.get("/wms/proxy")
def wms_tile_proxy(
    service: str = Query("WMS"),
    request: str = Query("GetMap"),
    layers: str = Query(...),
    styles: str = Query(""),
    format: str = Query("image/png"),
    transparent: str = Query("true"),
    version: str = Query("1.1.1"),
    width: str = Query("256"),
    height: str = Query("256"),
    srs: str = Query("EPSG:3857"),
    bbox: str = Query(...)
):
    from fastapi.responses import Response
    import requests

    incois_url = "https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms"
    params = {"service": service, "request": request, "layers": layers, "styles": styles, "format": format, "transparent": transparent, "version": version, "width": width, "height": height, "srs": srs, "bbox": bbox}
    try:
        res = requests.get(incois_url, params=params, timeout=30)
        res.raise_for_status()
        return Response(content=res.content, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WMS Proxy failed: {str(e)}")"""

new_func = """@router.get("/wms/proxy")
def wms_tile_proxy(
    service: str = Query("WMS"),
    request: str = Query("GetMap"),
    layers: str = Query(...),
    styles: str = Query(""),
    format: str = Query("image/png"),
    transparent: str = Query("true"),
    version: str = Query("1.1.1"),
    width: str = Query("256"),
    height: str = Query("256"),
    srs: str = Query("EPSG:3857"),
    bbox: str = Query(...)
):
    from fastapi.responses import Response
    import requests
    import os
    import hashlib
    import time

    cache_dir = "data/cache/wms_tiles"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create deterministic hash based on layer and bbox
    cache_key = f"{layers}_{bbox}_{width}x{height}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f"{cache_hash}.png")

    # Check cache (12-hour TTL to match daily INCOIS updates)
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < 12 * 3600:
            with open(cache_file, "rb") as f:
                return Response(content=f.read(), media_type="image/png")

    incois_url = "https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms"
    params = {"service": service, "request": request, "layers": layers, "styles": styles, "format": format, "transparent": transparent, "version": version, "width": width, "height": height, "srs": srs, "bbox": bbox}
    
    # Try 3 times with exponential backoff for INCOIS instability
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            res = requests.get(incois_url, params=params, timeout=10)
            res.raise_for_status()
            
            # Cache the successful response
            with open(cache_file, "wb") as f:
                f.write(res.content)
                
            return Response(content=res.content, media_type="image/png")
        except Exception as e:
            last_error = e
            time.sleep(1.0 * (attempt + 1))
            
    # If all retries failed, return an empty transparent 1x1 PNG so MapLibre doesn't throw 500s and block rendering
    empty_png = b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\x08\\x06\\x00\\x00\\x00\\x1f\\x15\\xc4\\x89\\x00\\x00\\x00\\nIDATx\\x9cc\\x00\\x01\\x00\\x00\\x05\\x00\\x01\\r\\n-\\xb4\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82'
    return Response(content=empty_png, media_type="image/png")"""

content = content.replace(old_func, new_func)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(content)
