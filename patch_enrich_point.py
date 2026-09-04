import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

# Change signature
content = content.replace(
    'def enrich_point(cls, lat: float, lon: float, timestamp: Optional[str] = None) -> Dict[str, Any]:',
    'def enrich_point(cls, lat: float, lon: float, timestamp: Optional[str] = None, shutdown_event=None) -> Dict[str, Any]:'
)

find_sst = '''        # Attempt WMS GetFeatureInfo for SST
        try:
            sst_res = INCOISGeoServerClient.get_feature_info(grid_lat, grid_lon, "PFZ-TUNA-SST-CHL:sst")'''
replace_sst = '''        if shutdown_event and shutdown_event.is_set(): raise InterruptedError("Shutdown")
        # Attempt WMS GetFeatureInfo for SST
        try:
            sst_res = INCOISGeoServerClient.get_feature_info(grid_lat, grid_lon, "PFZ-TUNA-SST-CHL:sst")'''
content = content.replace(find_sst, replace_sst)

find_chl = '''        # Attempt WMS GetFeatureInfo for Chlorophyll-a
        try:
            chl_res = INCOISGeoServerClient.get_feature_info(grid_lat, grid_lon, "PFZ-TUNA-SST-CHL:chl")'''
replace_chl = '''        if shutdown_event and shutdown_event.is_set(): raise InterruptedError("Shutdown")
        # Attempt WMS GetFeatureInfo for Chlorophyll-a
        try:
            chl_res = INCOISGeoServerClient.get_feature_info(grid_lat, grid_lon, "PFZ-TUNA-SST-CHL:chl")'''
content = content.replace(find_chl, replace_chl)

find_opendap = '''        # Step 4: Tier 3 Fallback (INCOIS OPeNDAP Grids - WW3 & Currents)'''
replace_opendap = '''        if shutdown_event and shutdown_event.is_set(): raise InterruptedError("Shutdown")
        # Step 4: Tier 3 Fallback (INCOIS OPeNDAP Grids - WW3 & Currents)'''
content = content.replace(find_opendap, replace_opendap)

find_write = '''        # Atomic write back to memory + disk
        with cls._lock:'''
replace_write = '''        if shutdown_event and shutdown_event.is_set(): raise InterruptedError("Shutdown")
        # Atomic write back to memory + disk
        with cls._lock:'''
content = content.replace(find_write, replace_write)

find_fetch_pt = '''            try:
                return coord, cls.enrich_point(lat, lon, timestamp=iso_timestamp)'''
replace_fetch_pt = '''            try:
                return coord, cls.enrich_point(lat, lon, timestamp=iso_timestamp, shutdown_event=shutdown_event)'''
content = content.replace(find_fetch_pt, replace_fetch_pt)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
