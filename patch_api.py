import re

with open("frontend/src/services/api.js", "r") as f:
    content = f.read()

injection = """
/** 13. Get Nearby Landing Centers */
export async function getNearbyLandingCenters(lat, lon, limit = 50) {
  const data = await fetchJson(getApiUrl(`/api/landing-centers/nearby?lat=${lat}&lon=${lon}&limit=${limit}`));
  if (data && Array.isArray(data)) return data;
  throw new Error('Invalid Landing Centers payload');
}
"""

if "getNearbyLandingCenters" not in content:
    content += injection
    with open("frontend/src/services/api.js", "w") as f:
        f.write(content)
