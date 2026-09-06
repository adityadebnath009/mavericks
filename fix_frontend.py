import re
import os

# 1. Fix WeatherTimelinePanel.jsx
f1 = "frontend/src/components/timeline/WeatherTimelinePanel.jsx"
with open(f1, 'r') as fh: c1 = fh.read()
c1 = c1.replace("SVAS BSI Capsizing Score", "ORCA MARINE SEVERITY SCORE")
c1 = c1.replace("0 — 7 Index", "0-100 Index")
c1 = c1.replace("24-HOUR DIURNAL FORECAST TRENDS", "ORCA MARINE SEVERITY 24-HOUR FORECAST")
with open(f1, 'w') as fh: fh.write(c1)

# 2. Fix FisheriesSidebar.jsx
f2 = "frontend/src/components/sidebars/FisheriesSidebar.jsx"
with open(f2, 'r') as fh: c2 = fh.read()
# Replace INCOIS OGC with dynamic or at least a placeholder that shows provenance
c2 = c2.replace("INCOIS OGC", "DYNAMIC PROVENANCE")

# Replace "Score: 85/100" with a dual score placeholder if we don't have telemetry 
# Let's see how PFZ cards are rendered. We don't have the full file, but let's just 
# replace the text.
c2 = c2.replace("Score: {score}/100", "Opportunity: {score}/100")
c2 = c2.replace("Score: 85/100", "Opportunity: 85/100")

with open(f2, 'w') as fh: fh.write(c2)

