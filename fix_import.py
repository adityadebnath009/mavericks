import re

with open("backend/app/api/services/orca_bsi_engine.py", "r") as f:
    content = f.read()

content = content.replace("from backend.app.core.domain", "from app.core.domain")

with open("backend/app/api/services/orca_bsi_engine.py", "w") as f:
    f.write(content)
