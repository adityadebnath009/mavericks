with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Replace the access block
old_block = """                access = dataset.find("thredds:access[@serviceName='opendap']", namespace)
                if access is not None:
                    url_path = access.attrib.get("urlPath")
                    if url_path:
                        base = catalog_url.split("/thredds/")[0]
                        dods_url = f"{base}/thredds/dodsC/{url_path}"
                        candidates.append((name, dods_url))"""

new_block = """                # Check for explicit access tag first
                url_path = None
                access = dataset.find("thredds:access[@serviceName='opendap']", namespace)
                if access is not None:
                    url_path = access.attrib.get("urlPath")
                
                # Fallback to direct urlPath attribute (new INCOIS THREDDS format)
                if not url_path:
                    url_path = dataset.attrib.get("urlPath")
                    
                if url_path:
                    base = catalog_url.split("/thredds/")[0]
                    dods_url = f"{base}/thredds/dodsC/{url_path}"
                    candidates.append((name, dods_url))"""

content = content.replace(old_block, new_block)

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
