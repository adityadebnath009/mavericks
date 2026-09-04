import re

def clean_file(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()
        
    # Remove global suppressions
    clean_lines = [line for line in lines if not ("import urllib3" in line or "urllib3.disable_warnings" in line)]
    content = "".join(clean_lines)
    
    # Remove verify=False
    content = content.replace(", verify=False)", ")")
    
    with open(filepath, "w") as f:
        f.write(content)

clean_file("backend/app/api/endpoints/incois_proxy.py")
clean_file("backend/app/api/services/incois_resolver.py")
