import requests
import xarray as xr
from datetime import datetime, timedelta

LAT, LON = 12.5, 71.5

print("--- TEST 1 & 2: WMS GetFeatureInfo ---")
def test_wms(layer):
    url = "https://incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/ows"
    params = {
        "service": "WMS",
        "version": "1.1.1",
        "request": "GetFeatureInfo",
        "layers": layer,
        "query_layers": layer,
        "info_format": "application/json",
        "srs": "EPSG:4326",
        "x": 50,
        "y": 50,
        "width": 100,
        "height": 100,
        "bbox": f"{LON-0.01},{LAT-0.01},{LON+0.01},{LAT+0.01}"
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            if features:
                val = features[0].get("properties", {}).get("GRAY_INDEX")
                print(f"{layer}: SUCCESS (Value: {val})")
            else:
                print(f"{layer}: SUCCESS (No features returned)")
        else:
            print(f"{layer}: FAILED HTTP {r.status_code}")
    except Exception as e:
        print(f"{layer}: TIMEOUT/ERROR - {e}")

test_wms("PFZ-TUNA-SST-CHL:sst")
test_wms("PFZ-TUNA-SST-CHL:chl")

print("\n--- TEST 3 & 4: OPeNDAP xarray ---")
def get_opendap_url(base_template):
    for lag in [0, 1, 2, 3]:
        dstr = (datetime.utcnow() - timedelta(days=lag)).strftime("%Y%m%d")
        url = base_template.format(dstr)
        try:
            requests.get(url + ".dds", timeout=2)
            return url
        except:
            pass
    return None

ww3_base = "https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_{}.nc"
ww3_url = get_opendap_url(ww3_base)
if ww3_url:
    print(f"Testing WW3 URL: {ww3_url}")
    try:
        # Crucially specifying engine="netcdf4" to use OPeNDAP
        ds = xr.open_dataset(ww3_url, engine="netcdf4")
        print("WW3 OPeNDAP: SUCCESS (Opened successfully with netcdf4 engine)")
    except Exception as e:
        print(f"WW3 OPeNDAP: FAILED - {e}")
else:
    print("WW3 OPeNDAP: FAILED to find valid URL")

curr_base = "https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_{}.nc"
curr_url = get_opendap_url(curr_base)
if curr_url:
    print(f"Testing Currents URL: {curr_url}")
    try:
        ds = xr.open_dataset(curr_url, engine="netcdf4")
        print("Currents OPeNDAP: SUCCESS")
    except Exception as e:
        print(f"Currents OPeNDAP: FAILED - {e}")
else:
    print("Currents OPeNDAP: FAILED to find valid URL")
