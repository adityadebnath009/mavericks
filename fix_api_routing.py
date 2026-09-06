import re
import os

f = "frontend/src/services/api.js"
with open(f, 'r') as fh: c = fh.read()

replacement = """
export async function calculateRoute(start, end, beam = 3.5, day = 1, hour = 12) {
  const dt = new Date();
  dt.setDate(dt.getDate() + (day - 1));
  dt.setUTCHours(hour, 0, 0, 0);
  
  const data = await fetchJson(getApiUrl('/api/routing/safe-route'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin: { lat: start.lat, lon: start.lon },
      destination: { lat: end.lat, lon: end.lon },
      vessel_profile: { length_m: beam * 5.0, beam_m: beam, cruising_speed_kn: 10.0 },
      departure_time: dt.toISOString(),
      optimize_departure: false
    })
  });
  if (data && data.path) return data;
  throw new Error('Malformed route data or no safe route found.');
}
"""

c = re.sub(r'export async function calculateRoute.*?\n\}', replacement.strip(), c, flags=re.DOTALL)
with open(f, 'w') as fh: fh.write(c)

