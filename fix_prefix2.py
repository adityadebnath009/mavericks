import re

with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Fix the prefixes
content = content.replace(
    'latest = cls._get_latest_catalog_dataset(url, "io_ww3_")',
    'latest = cls._get_latest_catalog_dataset(url, "rsmc_nio_ww3_")'
)
content = content.replace(
    'latest = cls._get_latest_catalog_dataset(url, "CURRENTS_IO_")',
    'latest = cls._get_latest_catalog_dataset(url, "CURRENTS_NIO_")'
)

# Update `_extract_forecast_cycle`
content = content.replace('.replace("io_ww3_", "").replace("CURRENTS_IO_", "")', '.replace("rsmc_nio_ww3_", "").replace("CURRENTS_NIO_", "")')

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
