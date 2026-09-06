with open("frontend/src/services/api.js", "r") as f:
    content = f.read()

old_func = """export async function calculateRoute(start, end, beam = 3.5, day = 1, hour = 12) {
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
}"""

new_func = """export async function calculateRoute(start, end, vesselProfile, departureTimeStr) {
  const data = await fetchJson(getApiUrl('/api/routing/safe-route'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin: { lat: start.lat, lon: start.lon },
      destination: { lat: end.lat, lon: end.lon },
      vessel_profile: vesselProfile,
      departure_time: departureTimeStr || new Date().toISOString(),
      optimize_departure: false
    })
  });
  if (data && data.path) return data;
  throw new Error('Malformed route data or no safe route found.');
}"""

content = content.replace(old_func, new_func)

with open("frontend/src/services/api.js", "w") as f:
    f.write(content)
print("api.js patched")
