import re

with open("backend/app/api/endpoints/safety.py", "r") as f:
    content = f.read()

# We'll just modify the frontend if needed, but for the backend we should provide a clean ORCA based endpoint
