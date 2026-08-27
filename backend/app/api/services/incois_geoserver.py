import os
import json
import time
import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../cache"))
CAPABILITIES_CACHE_PATH = os.path.join(CACHE_DIR, "incois_capabilities.json")
WFS_CACHE_PATH = os.path.join(CACHE_DIR, "incois_pfzlines.json")

# Verified fallback layers in case INCOIS server is offline
FALLBACK_LAYERS = [
    {
        "name": "PFZ-TUNA-SST-CHL:sst",
        "title": "sst",
        "abstract": "Sea Surface Temperature observations derived from satellite data.",
        "queryable": True
    },
    {
        "name": "PFZ-TUNA-SST-CHL:chl",
        "title": "chl",
        "abstract": "Chlorophyll observations derived from satellite data.",
        "queryable": True
    },
    {
        "name": "PFZ-TUNA-SST-CHL:pfz_tuna_chl_sld",
        "title": "Chlorophyll Concentration (mg/m3)",
        "abstract": "Chlorophyll concentration maps styled for PFZ advisory use.",
        "queryable": True
    },
    {
        "name": "PFZ-TUNA-SST-CHL:PFZ-TUNA-CHL-SST",
        "title": "Sea Surface Temperature Styled",
        "abstract": "Authoritative Sea Surface Temperature styled raster maps.",
        "queryable": True
    },
    {
        "name": "PFZ_Automation:pfzlines",
        "title": "pfzlines",
        "abstract": "Official Potential Fishing Zone (PFZ) advisory vector contours.",
        "queryable": True
    }
]

class INCOISGeoServerClient:
    """
    Authoritative OGC client for parsing INCOIS WMS capabilities,
    running GetFeatureInfo coordinate inspections, and fetching WFS vectors.
    """

    @staticmethod
    def get_capabilities() -> dict:
        """
        Retrieves available WMS layers from the INCOIS GeoServer.
        Uses cached responses if valid (24h TTL) or falls back to standard presets.
        """
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Check cache validity
        if os.path.exists(CAPABILITIES_CACHE_PATH):
            try:
                with open(CAPABILITIES_CACHE_PATH, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    # Use cache if within 24 hours (86400 seconds)
                    if time.time() - cached.get("timestamp", 0) < 86400:
                        return cached
            except Exception as e:
                logger.error(f"Error reading capabilities cache: {e}")

        # Fetch fresh Capabilities XML
        url = "https://incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/ows"
        params = {
            "service": "WMS",
            "request": "GetCapabilities"
        }
        
        try:
            r = requests.get(url, params=params, timeout=8)
            if r.status_code == 200:
                # Parse XML capabilities
                root = ET.fromstring(r.content)
                
                # Namespace handling (often default namespace is http://www.opengis.net/wms)
                ns = {'wms': 'http://www.opengis.net/wms'}
                layers_found = []
                
                # Search for Layer elements
                for layer_el in root.findall(".//wms:Layer", ns):
                    name_el = layer_el.find("wms:Name", ns)
                    title_el = layer_el.find("wms:Title", ns)
                    abstract_el = layer_el.find("wms:Abstract", ns)
                    queryable = layer_el.attrib.get("queryable") == "1"
                    
                    if name_el is not None and title_el is not None:
                        layers_found.append({
                            "name": name_el.text,
                            "title": title_el.text,
                            "abstract": abstract_el.text if abstract_el is not None else "",
                            "queryable": queryable
                        })
                
                # Include standard PFZ Automation layer
                layers_found.append({
                    "name": "PFZ_Automation:pfzlines",
                    "title": "pfzlines",
                    "abstract": "Authoritative Potential Fishing Zone contour paths.",
                    "queryable": True
                })
                
                result = {
                    "source": "INCOIS GeoServer",
                    "status": "online",
                    "timestamp": time.time(),
                    "layers": layers_found
                }
                
                # Write cache
                with open(CAPABILITIES_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch capabilities from INCOIS GeoServer: {e}")

        # Offline fallback
        logger.warning("Using offline fallback data metadata for INCOIS GeoServer.")
        
        # Load from expired cache if exists, otherwise fallback to static presets
        if os.path.exists(CAPABILITIES_CACHE_PATH):
            try:
                with open(CAPABILITIES_CACHE_PATH, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    cached["status"] = "stale"
                    return cached
            except Exception:
                pass

        return {
            "source": "INCOIS GeoServer fallback",
            "status": "offline",
            "timestamp": time.time(),
            "layers": FALLBACK_LAYERS
        }

    @staticmethod
    def get_feature_info(lat: float, lon: float, layer: str) -> dict:
        """
        Performs a WMS GetFeatureInfo point query at given coordinates
        to inspect numerical SST or Chlorophyll values directly from INCOIS raster assets.
        """
        # Set up a small bounding box (0.01 degree) centered on coordinate
        delta = 0.005
        bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
        
        url = "https://incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/ows"
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer,
            "QUERY_LAYERS": layer,
            "BBOX": bbox,
            "WIDTH": "101",
            "HEIGHT": "101",
            "X": "50",
            "Y": "50",
            "SRS": "EPSG:4326",
            "INFO_FORMAT": "application/json"
        }
        
        try:
            r = requests.get(url, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                features = data.get("features", [])
                if features:
                    properties = features[0].get("properties", {})
                    # GeoServer outputs index values as GRAY_INDEX
                    val = properties.get("GRAY_INDEX")
                    if val is not None:
                        return {
                            "status": "success",
                            "value": float(val),
                            "layer": layer,
                            "coordinate": {"lat": lat, "lon": lon},
                            "timestamp": time.time()
                        }
                return {
                    "status": "no_data",
                    "message": "No data found at this coordinate.",
                    "layer": layer
                }
        except Exception as e:
            logger.error(f"GetFeatureInfo request failed for {layer} at {lat},{lon}: {e}")
            
        return {
            "status": "error",
            "message": "INCOIS GeoServer unreachable or timed out.",
            "layer": layer
        }

    @staticmethod
    def get_pfz_lines_wfs() -> dict:
        """
        Queries the WFS service to retrieve dynamic PFZ lines in GeoJSON format.
        Caches results locally to survive network downtime.
        """
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # 1. Try fetching fresh WFS GeoJSON
        url = "https://incois.gov.in/geoserver/PFZ_Automation/ows"
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": "PFZ_Automation:pfzlines",
            "outputFormat": "application/json"
        }
        
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                geojson_data = r.json()
                # Cache successful request
                with open(WFS_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(geojson_data, f, indent=2)
                return geojson_data
        except Exception as e:
            logger.error(f"Failed to fetch PFZ lines WFS from INCOIS: {e}")

        # 2. Offline fallback from local cache file
        if os.path.exists(WFS_CACHE_PATH):
            try:
                with open(WFS_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as ex:
                logger.error(f"Error loading cached WFS lines: {ex}")
                
        # Empty GeoJSON FeatureCollection fallback
        return {
            "type": "FeatureCollection",
            "features": [],
            "note": "Offline fallback - No cached PFZ Advisory lines available."
        }
