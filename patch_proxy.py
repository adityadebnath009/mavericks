import re

with open("backend/app/api/endpoints/incois_proxy.py", "r") as f:
    content = f.read()

# Replace the resolve_vector_grid call with a pure static file read
old_block = """    data = IncoisDatasetResolver.resolve_vector_grid(day=day, hour=hour)
    data["source"] = "INCOIS WW3 + Currents (cache)" if cache_was_fresh else "INCOIS WW3 + Currents"
    data["cache"] = cache_was_fresh
    return data"""

new_block = """    import json
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["source"] = "INCOIS WW3 + Currents (cache)"
        data["cache"] = True
        return data
    else:
        raise HTTPException(status_code=503, detail="Vector grid cache expired and PyDAP generation is disabled in P1.2")"""

content = content.replace(old_block, new_block)

with open("backend/app/api/endpoints/incois_proxy.py", "w") as f:
    f.write(content)
