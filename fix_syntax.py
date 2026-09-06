import re

f = "frontend/src/services/api.js"
with open(f, 'r') as fh: c = fh.read()

# I will just carefully replace the broken chunk.
broken_chunk = """
/** 11b. Legacy stub */
export async function getPointAnalytics(lat, lon) {
  return getTelemetry(lat, lon);
}&lon=${lon}`));
  if (data && data.metrics) return data;
  throw new Error('Malformed point-analytics payload');
}
"""
fixed_chunk = """
/** 11b. Legacy stub */
export async function getPointAnalytics(lat, lon) {
  return getTelemetry(lat, lon);
}
"""

c = c.replace(broken_chunk.strip(), fixed_chunk.strip())

with open(f, 'w') as fh: fh.write(c)

