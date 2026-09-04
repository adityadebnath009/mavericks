import re

with open("backend/app/api/services/incois_client.py", "r") as f:
    content = f.read()

find = '''    def send(self, request, **kwargs):
        from urllib.parse import urlparse'''

replace = '''    def send(self, request, **kwargs):
        from urllib.parse import urlparse
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = (3.0, 10.0)'''

content = content.replace(find, replace)

with open("backend/app/api/services/incois_client.py", "w") as f:
    f.write(content)
