import requests

try:
    print(requests.get("https://incois.gov.in/thredds/catalog.xml", verify=False, timeout=10).text)
except Exception as e:
    print("Error:", e)
