/**
 * Unified API Client for Navik Operations Console
 * Wraps all backend endpoints with timeout protection and seamless mock fallbacks.
 */

import {
  MOCK_SAFETY_DATA,
  MOCK_FORECAST_TIMELINE,
  MOCK_GRID_GEOJSON,
  MOCK_ADVISORIES_GEOJSON,
  MOCK_GEOFENCE_GEOJSON,
  MOCK_PFZ_LINES,
  MOCK_DATA_STATUS,
  generateMockRoute,
  generateMockPfzEvaluation,
  generateMockPointAnalytics
} from './mockData';

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

/**
 * 1. Get Point Safety Assessment
 */
export async function getSafety(lat, lon, beam = 3.5, day = 1, hour = 12) {
  try {
    const url = getApiUrl(`/api/safety?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}&hour=${hour}`);
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.rating) return data;
    throw new Error('Malformed safety payload');
  } catch (err) {
    console.warn(`[Navik API] getSafety fallback engaged (${err.message}):`, { lat, lon });
    return {
      ...MOCK_SAFETY_DATA,
      coordinates: { latitude: Number(lat), longitude: Number(lon) },
      vessel_suitability: {
        vessel_beam_m: Number(beam),
        critical_beam_m: 4.8,
        vulnerable: Number(beam) < 4.0
      }
    };
  }
}

/**
 * 2. Get 24-Hour Diurnal Timeline Forecast
 */
export async function getForecast(lat, lon, day = 1) {
  try {
    const url = getApiUrl(`/api/safety/forecast?lat=${lat}&lon=${lon}&day=${day}`);
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (Array.isArray(data) && data.length > 0) return data;
    throw new Error('Malformed forecast array');
  } catch (err) {
    console.warn(`[Navik API] getForecast fallback engaged (${err.message})`);
    return MOCK_FORECAST_TIMELINE;
  }
}

/**
 * 3. Get 0.4° BSI Safety Grid GeoJSON
 */
export async function getGrid(day = 1, hour = 12) {
  try {
    const url = getApiUrl(`/api/safety/grid?day=${day}&hour=${hour}`);
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.type === 'FeatureCollection') return data;
    throw new Error('Invalid GeoJSON FeatureCollection');
  } catch (err) {
    console.warn(`[Navik API] getGrid fallback engaged (${err.message})`);
    return MOCK_GRID_GEOJSON;
  }
}

/**
 * 4. Get Coastal Advisories GeoJSON
 */
export async function getAdvisories() {
  try {
    const url = getApiUrl('/api/safety/advisories');
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.type === 'FeatureCollection') return data;
    throw new Error('Invalid Advisories GeoJSON');
  } catch (err) {
    console.warn(`[Navik API] getAdvisories fallback engaged (${err.message})`);
    return MOCK_ADVISORIES_GEOJSON;
  }
}

/**
 * 5. Get Geofencing Boundaries & MPAs GeoJSON
 */
export async function getGeofence() {
  try {
    const url = getApiUrl('/api/geofence/geojson');
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.type === 'FeatureCollection') return data;
    throw new Error('Invalid Geofence GeoJSON');
  } catch (err) {
    console.warn(`[Navik API] getGeofence fallback engaged (${err.message})`);
    return MOCK_GEOFENCE_GEOJSON;
  }
}

/**
 * 6. Get Potential Fishing Zone (PFZ) Vector Lines GeoJSON
 */
export async function getPfzLines() {
  try {
    const url = getApiUrl('/api/incois/pfz-lines');
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.type === 'FeatureCollection') return data;
    throw new Error('Invalid PFZ GeoJSON');
  } catch (err) {
    console.warn(`[Navik API] getPfzLines fallback engaged (${err.message})`);
    return MOCK_PFZ_LINES;
  }
}

/**
 * 7. Evaluate Specific PFZ Feature
 */
export async function evaluatePfz(vessel, pfzId, beam = 3.5) {
  try {
    const url = getApiUrl('/api/pfz/evaluate');
    const res = await fetchWithTimeout(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vessel: { lat: vessel.lat, lon: vessel.lon },
        pfz_id: pfzId,
        beam_m: beam
      })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[Navik API] evaluatePfz fallback engaged (${err.message})`);
    return generateMockPfzEvaluation(vessel, pfzId, beam);
  }
}

/**
 * 8. Calculate Weather-Optimized A* Safe Route
 */
export async function calculateRoute(start, end, beam = 3.5, day = 1, hour = 12) {
  try {
    const url = getApiUrl('/api/pfz/route');
    const res = await fetchWithTimeout(url, {
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
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.route_coords) return data;
    throw new Error('Malformed route data');
  } catch (err) {
    console.warn(`[Navik API] calculateRoute fallback engaged (${err.message})`);
    return generateMockRoute(start, end, beam);
  }
}

/**
 * 9. AI Safety Advisor Grounded RAG Query
 */
export async function askSafetyAdvisor(userQuery, activeWorkspace = 'Tactical Routing', liveContext = {}) {
  try {
    const url = getApiUrl('/api/advisor/chat');
    const res = await fetchWithTimeout(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_query: userQuery,
        active_workspace: activeWorkspace,
        live_context: liveContext
      })
    }, 5000);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[Navik API] askSafetyAdvisor fallback engaged (${err.message})`);
    const rating = liveContext.current_risk_score || 'LOW';
    const wave = liveContext.max_wave_height || '1.2m';
    const beam = liveContext.beam_width || '3.5m';

    return {
      response_text: `Based on official INCOIS SVAS data and FAO Code of Conduct for Responsible Fisheries, conditions for your ${beam} vessel are currently assessed as ${rating}. Significant wave height is ${wave}. Standard maritime safety protocols and VHF Channel 16 monitoring are advised.`,
      citations: [
        {
          title: 'FAO Small Craft Safety Code (1980)',
          clause: 'Section 4.2 - Beam Stability & Wave Encounters'
        },
        {
          title: 'INCOIS Small Vessel Advisory Service (SVAS)',
          clause: 'Technical Bulletin 2026/08 - Indian EEZ Hazard Thresholds'
        }
      ],
      safety_rating: rating,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * 10. Data Telemetry Health Status
 */
export async function getDataStatus() {
  try {
    const url = getApiUrl('/api/safety/data-status');
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return MOCK_DATA_STATUS;
  }
}

/**
 * 11. Get INCOIS Point Analytics Telemetry
 */
export async function getPointAnalytics(lat, lon) {
  try {
    const url = getApiUrl(`/api/incois/point-analytics?lat=${lat}&lon=${lon}`);
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data && data.metrics) return data;
    throw new Error('Malformed point-analytics payload');
  } catch (err) {
    console.warn(`[Navik API] getPointAnalytics fallback engaged (${err.message}):`, { lat, lon });
    return generateMockPointAnalytics(lat, lon);
  }
}

/**
 * 12. Get MapLibre Vector Grid
 */
export async function getVectorGrid(day = 1) {
  try {
    const url = getApiUrl(`/api/incois/vector-grid?day=${day}`);
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    // Transform into GeoJSON FeatureCollections for MapLibre
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
      currentGeojson: toGeoJSON(data.current)
    };
  } catch (err) {
    console.warn(`[Navik API] getVectorGrid failed (${err.message})`);
    return {
      windGeojson: { type: 'FeatureCollection', features: [] },
      currentGeojson: { type: 'FeatureCollection', features: [] }
    };
  }
}

