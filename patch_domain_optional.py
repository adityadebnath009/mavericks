import re

with open("backend/app/core/domain.py", "r") as f:
    content = f.read()

content = content.replace("current: EnvironmentalConditions", "current: Optional[EnvironmentalConditions] = None")
content = content.replace("timeline: TimelineSeries", "timeline: Optional[TimelineSeries] = None")
content = content.replace("provenance: Dict[str, ProvenanceRecord]", "provenance: Optional[Dict[str, ProvenanceRecord]] = None")

with open("backend/app/core/domain.py", "w") as f:
    f.write(content)
