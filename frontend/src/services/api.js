/**
 * Unified API Client for Navik Operations Console.
 * Backend failures are propagated to the dashboard so the UI can truthfully
 * distinguish live data from unavailable data.
 */

const API_TIMEOUT_MS = 15000;

export const getApiUrl = (path) => {
  if (typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location;
    if (protocol === 'file:' || ((hostname === 'localhost' || hostname === '127.0.0.1') && port !== '8000')) {
      return `http://127.0.0.1:8000${path}`;
    }
  }
  return path;
};

async function fetchWithTimeout(url, options = {}, timeoutMs = API_TIMEOUT_MS) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

async function fetchJson(url, options = {}, timeoutMs = API_TIMEOUT_MS) {
  const res = await fetchWithTimeout(url, options, timeoutMs);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** 1. Get Point Safety Assessment */
export async function getSafety(lat, lon, beam = 3.5, day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl(`/api/safety?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}&hour=${hour}`));
  if (data && data.rating) return data;
  throw new Error('Malformed safety payload');
}

/** 2. Get 24-Hour Diurnal Timeline Forecast */
export async function getForecast(lat, lon, day = 1) {
  const data = await fetchJson(getApiUrl(`/api/safety/forecast?lat=${lat}&lon=${lon}&day=${day}`));
  if (Array.isArray(data) && data.length > 0) return data;
  throw new Error('Malformed forecast array');
}

/** 3. Get 0.4° BSI Safety Grid GeoJSON */
export async function getGrid(day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl(`/api/safety/grid?day=${day}&hour=${hour}`));
  if (data && data.type === 'FeatureCollection') return data;
  throw new Error('Invalid GeoJSON FeatureCollection');
}

/** 4. Get Coastal Advisories GeoJSON */
export async function getAdvisories() {
  const data = await fetchJson(getApiUrl('/api/safety/advisories'));
  if (data && data.type === 'FeatureCollection') return data;
  throw new Error('Invalid Advisories GeoJSON');
}

/** 5. Get Geofencing Boundaries & MPAs GeoJSON */
export async function getGeofence() {
  const data = await fetchJson(getApiUrl('/api/geofence/geojson'));
  if (data && data.type === 'FeatureCollection') return data;
  throw new Error('Invalid Geofence GeoJSON');
}

/** 6. Get Potential Fishing Zone (PFZ) Vector Lines GeoJSON */
export async function getPfzLines() {
  const data = await fetchJson(getApiUrl('/api/incois/pfz-lines'));
  if (data && data.type === 'FeatureCollection') return data;
  throw new Error('Invalid PFZ GeoJSON');
}

/** 7. Evaluate Specific PFZ Feature */
export async function evaluatePfz(vessel, pfzId, beam = 3.5) {
  const url = getApiUrl('/api/pfz/evaluate');
  return fetchJson(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      vessel: { lat: vessel.lat, lon: vessel.lon },
      pfz_id: pfzId,
      beam_m: beam
    })
  });
}

/** 8. Calculate Weather-Optimized A* Safe Route */
export async function calculateRoute(start, end, beam = 3.5, day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl('/api/pfz/route'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start: { lat: start.lat, lon: start.lon },
      end: { lat: end.lat, lon: end.lon },
      beam_m: beam,
      day,
      hour
    })
  });
  if (data && data.route_coords) return data;
  throw new Error('Malformed route data');
}

/** 9. AI Safety Advisor Grounded RAG Query */
export async function askSafetyAdvisor(userQuery, activeWorkspace = 'Tactical Routing', liveContext = {}) {
  return fetchJson(getApiUrl('/api/advisor/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_query: userQuery,
      active_workspace: activeWorkspace,
      live_context: liveContext
    })
  }, 5000);
}

/** 10. Data Telemetry Health Status */
export async function getDataStatus() {
  return fetchJson(getApiUrl('/api/safety/data-status'));
}

/** 11. Get INCOIS Point Analytics Telemetry */
export async function getPointAnalytics(lat, lon) {
  const data = await fetchJson(getApiUrl(`/api/incois/point-analytics?lat=${lat}&lon=${lon}`));
  if (data && data.metrics) return data;
  throw new Error('Malformed point-analytics payload');
}

/** 12. Get MapLibre Vector Grid for an exact forecast day/hour. */
export async function getVectorGrid(day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl(`/api/incois/vector-grid?day=${day}&hour=${hour}`));

  const toGeoJSON = (arr) => ({
    type: 'FeatureCollection',
    features: (arr || []).map(p => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
      properties: { ...p }
    }))
  });

  return {
    windGeojson: toGeoJSON(data.wind),
    currentGeojson: toGeoJSON(data.current),
    timestamp: data.timestamp || null
  };
}
