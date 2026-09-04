import urllib.request
import xml.etree.ElementTree as ET

url = "https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/ows?service=WMS&version=1.1.1&request=GetCapabilities"
response = urllib.request.urlopen(url)
xml_data = response.read()
root = ET.fromstring(xml_data)

for layer in root.findall('.//Layer'):
    name = layer.find('Name')
    if name is not None:
        print(name.text)
