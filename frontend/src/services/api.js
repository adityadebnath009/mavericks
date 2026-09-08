/**
 * Unified API Client for Navik Operations Console.
 * Backend failures are propagated to the dashboard so the UI can truthfully
 * distinguish live data from unavailable data.
 */

const API_TIMEOUT_MS = 60000; // Extended from 15s to 60s for heavy A* routing queries

export const getApiUrl = (path) => {
  // Always return the relative path. 
  // In dev, vite.config.js proxies /api to the backend.
  // In prod, the backend serves the frontend and the relative path works natively.
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
  if (!res.ok) {
    let errDetail = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errDetail = errJson.detail;
      }
    } catch (e) {}
    throw new Error(errDetail);
  }
  return res.json();
}

/** 1. Get Point Safety Assessment */
export async function getSafety(lat, lon, beam = 3.5, day = 1, hour = 12) {
  const data = await fetchJson(getApiUrl(`/api/safety?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}&hour=${hour}`));
  // ORCA BSI Engine uses severity_score instead of rating
  if (data && (data.rating || data.severity_score !== undefined)) return data;
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
export async function calculateRoute(start, end, vesselProfile, departureTimeStr) {
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

/** 11. Get Telemetry (Phase F1) */
export async function getTelemetry(lat, lon) {
  const data = await fetchJson(getApiUrl(`/api/telemetry/location?lat=${lat}&lon=${lon}`));
  if (data) return data;
  throw new Error('Malformed telemetry payload');
}

/** 11b. Legacy stub */
export async function getPointAnalytics(lat, lon) {
  return getTelemetry(lat, lon);
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

/** 13. Get Nearby Landing Centers */
export async function getNearbyLandingCenters(lat, lon, limit = 50) {
  const data = await fetchJson(getApiUrl(`/api/landing-centers/nearby?lat=${lat}&lon=${lon}&limit=${limit}`));
  if (data && Array.isArray(data.landing_centers)) return data.landing_centers;
  throw new Error('Invalid Landing Centers payload');
}
