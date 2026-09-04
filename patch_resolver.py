import re

with open("backend/tests/test_incois_resolver.py", "r") as f:
    content = f.read()

find = """        if "timeout" in err_msg.lower() or "connection" in err_msg.lower() or "netcdf" in err_msg.lower() or "i/o failure" in err_msg.lower():"""
replace = """        if "timeout" in err_msg.lower() or "timed out" in err_msg.lower() or "connection" in err_msg.lower() or "netcdf" in err_msg.lower() or "i/o failure" in err_msg.lower():"""

content = content.replace(find, replace)

with open("backend/tests/test_incois_resolver.py", "w") as f:
    f.write(content)
