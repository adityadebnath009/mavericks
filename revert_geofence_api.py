import re

with open("frontend/src/services/api.js", "r") as f:
    content = f.read()

old_block = """export async function getGeofence() {
  // Directly fetch the static JSON bundled in the frontend public folder
  // This prevents hitting the backend API for permanent/static boundaries!
  const res = await fetch('/boundaries.geojson');
  if (!res.ok) throw new Error('Geofence fallback missing');
  const data = await res.json();
  if (data && data.type === 'FeatureCollection') return data;
  throw new Error('Invalid Geofence GeoJSON');
}"""

new_block = """export async function getGeofence() {
  const data = await fetchJson(getApiUrl('/api/geofence/geojson'));
  if (data && data.type === 'FeatureCollection') return data;
  throw new Error('Invalid Geofence GeoJSON');
}"""

content = content.replace(old_block, new_block)

with open("frontend/src/services/api.js", "w") as f:
    f.write(content)
