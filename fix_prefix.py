import re

with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Fix the URLs again to be sure
content = content.replace(
    'url = "https://incois.gov.in/thredds/catalog/OOS/INCOIS_WW3/catalog.xml"',
    'url = "https://incois.gov.in/thredds/catalog/osf/ww3/catalog.xml"'
)
content = content.replace(
    'url = "https://incois.gov.in/thredds/catalog/OOS/Currents/catalog.xml"',
    'url = "https://incois.gov.in/thredds/catalog/osf/currents/catalog.xml"'
)

# Fix the prefixes
content = content.replace(
    'latest = cls._get_latest_catalog_dataset(url, "ww3_")',
    'latest = cls._get_latest_catalog_dataset(url, "io_ww3_")'
)
content = content.replace(
    'latest = cls._get_latest_catalog_dataset(url, "currents_")',
    'latest = cls._get_latest_catalog_dataset(url, "CURRENTS_IO_")'
)

# Also fix the extraction of the cycle.
# Previous: "ww3_20250930.nc" -> cycle was "20250930"
# Now: "io_ww3_20250930.nc" -> cycle is "20250930"
# Let's update `_extract_forecast_cycle`
old_extract = '''    @classmethod
    def _extract_forecast_cycle(cls, url: str) -> str:
        # Expected format: .../ww3_YYYYMMDD_HH.nc
        basename = url.split("/")[-1]
        return basename.replace(".nc", "")'''
        
new_extract = '''    @classmethod
    def _extract_forecast_cycle(cls, url: str) -> str:
        basename = url.split("/")[-1]
        return basename.replace(".nc", "").replace("io_ww3_", "").replace("CURRENTS_IO_", "")'''

content = content.replace(old_extract, new_extract)

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
