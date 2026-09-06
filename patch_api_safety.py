with open("frontend/src/services/api.js", "r") as f:
    content = f.read()

old_safety = """export async function getSafety(lat, lon, beam = 3.5, day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl(`/api/safety?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}&hour=${hour}`));
  if (data && data.rating) return data;
  throw new Error('Malformed safety payload');
}"""

new_safety = """export async function getSafety(lat, lon, beam = 3.5, day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl(`/api/safety?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}&hour=${hour}`));
  // ORCA BSI Engine uses severity_score instead of rating
  if (data && (data.rating || data.severity_score !== undefined)) return data;
  throw new Error('Malformed safety payload');
}"""

content = content.replace(old_safety, new_safety)

with open("frontend/src/services/api.js", "w") as f:
    f.write(content)
print("api.js patched for getSafety")
