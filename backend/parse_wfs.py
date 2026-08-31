import urllib.request
import xml.etree.ElementTree as ET

url = "https://incois.gov.in/geoserver/PFZ_Automation/ows?service=WFS&version=1.1.0&request=GetCapabilities"
response = urllib.request.urlopen(url)
xml_data = response.read()
root = ET.fromstring(xml_data)

ns = {'wfs': 'http://www.opengis.net/wfs'}
for feature_type in root.findall('.//wfs:FeatureType', ns):
    name = feature_type.find('wfs:Name', ns)
    if name is not None:
        print(name.text)
