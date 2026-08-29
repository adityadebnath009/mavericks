from datetime import datetime, timedelta
import urllib.request

for lag in [0, 1, 2, 3]:
    target_date = datetime.utcnow() - timedelta(days=lag)
    date_str = target_date.strftime("%Y%m%d")
    url = f"https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_{date_str}.nc.dds"
    try:
        urllib.request.urlopen(url, timeout=2)
        print(f"Found WW3 for lag {lag}: {url}")
        break
    except Exception as e:
        print(f"Failed lag {lag}: {url} -> {e}")

for lag in [0, 1, 2, 3, 4, 5]:
    target_date = datetime.utcnow() - timedelta(days=lag)
    date_str = target_date.strftime("%Y%m%d")
    url = f"https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_{date_str}.nc.dds"
    try:
        urllib.request.urlopen(url, timeout=2)
        print(f"Found Currents for lag {lag}: {url}")
        break
    except Exception as e:
        print(f"Failed lag {lag}: {url} -> {e}")
