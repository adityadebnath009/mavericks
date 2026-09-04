import os

def patch_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    if "urllib3.disable_warnings" not in content:
        injection = """
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
"""
        # Inject right after imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if not line.startswith('import ') and not line.startswith('from '):
                lines.insert(i, injection)
                break
        
        with open(filepath, "w") as f:
            f.write('\n'.join(lines))

patch_file("backend/app/api/endpoints/incois_proxy.py")
patch_file("backend/app/api/services/incois_resolver.py")
