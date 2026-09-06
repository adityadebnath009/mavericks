import re

f = "frontend/src/components/map/MapConsole.jsx"
with open(f, 'r') as fh: c = fh.read()

# Replace the duplicate `const source = ...` I introduced
bad_chunk = """
              // Fisheries Phase F1 Payload adapter
              const prov = res?.provenance || {};
              const source = prov?.sst?.source || 'Telemetry API';
"""
good_chunk = """
              // Fisheries Phase F1 Payload adapter
              const prov = res?.provenance || {};
              // using existing source variable
"""

c = c.replace(bad_chunk.strip(), good_chunk.strip())

with open(f, 'w') as fh: fh.write(c)

