with open("/Users/adityadebnath/.gemini/antigravity/brain/5bba35e8-b01b-4155-8daf-4834890a1ea4/task.md", "r") as f:
    content = f.read()

content = content.replace("[ ] Create `OrcaBsiEngine` skeleton class.", "[x] Create `OrcaBsiEngine` skeleton class.")
content = content.replace("[ ] Implement `VesselProfile` schema", "[x] Implement `VesselProfile` schema")
content = content.replace("[ ] Implement continuous steepness calculation", "[x] Implement continuous steepness calculation")
content = content.replace("[ ] Implement continuous rapid-development calculation", "[x] Implement continuous rapid-development calculation")
content = content.replace("[ ] Implement normalized vessel susceptibility function.", "[x] Implement normalized vessel susceptibility function.")
content = content.replace("[ ] Retain 0-7 bitmask explainability layer inside the engine.", "[x] Retain 0-7 bitmask explainability layer inside the engine.")
content = content.replace("[ ] Write `test_bsi_rapid_development.py`.", "[x] Write `test_bsi_rapid_development.py`.")
content = content.replace("[ ] Write `test_bsi_susceptibility_normalization.py`.", "[x] Write `test_bsi_susceptibility_normalization.py`.")

with open("/Users/adityadebnath/.gemini/antigravity/brain/5bba35e8-b01b-4155-8daf-4834890a1ea4/task.md", "w") as f:
    f.write(content)
