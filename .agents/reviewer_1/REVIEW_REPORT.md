# Adversarial Review & Improvement Record

**Working Directory:** `/Users/adityadebnath/Projects/mavericks/.agents/reviewer_1`  
**Target:** ORCA Marine Portal UI, Map Layers, Sidebars, and Recharts Graphs Restoral

---

## 1. What the Prior Attempt Got Wrong

### Issue 1: Missing Coordinate Selection on MPA (Restricted Area) Layer Click
- **Input:** User clicks inside a Marine Protected Area polygon on the map (e.g. Gulf of Mannar or Sundarbans).
- **Expected:** The application should display the sanctuary popup AND trigger `onLocationSelect({ lat, lon })`, moving the boat marker to the clicked position and updating the sidebar to show `DANGER_INSIDE_RESTRICTED_ZONE` with specific MPA safety warnings.
- **Actual:** The click handler for `mpa-fill` displayed the popup tooltip but omitted calling `onLocationSelect`. Furthermore, the general map click handler explicitly skipped calling `onLocationSelect` whenever `mpa-fill` was rendered under the click point. As a result, clicking inside an MPA did not update the vessel location or sidebar inspection values.
- **Root Cause:** Missing `onLocationSelect` invocation in `MapContainer.jsx` within the `map.on('click', 'mpa-fill')` callback.

### Issue 2: Crash Risk in `queryRenderedFeatures` with Unloaded Layer IDs
- **Input:** User clicks on the map before the asynchronous `geofence.geojson` fetch completes or if the network drops.
- **Expected:** Click event should safely inspect the ocean water coordinates without crashing MapLibre GL.
- **Actual:** `map.queryRenderedFeatures(e.point, { layers: ['bsi-grid-fill', 'mpa-fill'] })` threw an uncaught error if `mpa-fill` was not yet registered in the map's style sheet.
- **Root Cause:** Calling `queryRenderedFeatures` with hardcoded layer names that may not exist in the active style.

### Issue 3: Leaked / Overlapping Popups on Map Grid Interactions
- **Input:** User repeatedly clicks on multiple BSI risk grid cells or MPA zones.
- **Expected:** Only one active inspection tooltip popup should be visible at a time.
- **Actual:** Every click constructed `new maplibregl.Popup().addTo(map)` without removing or tracking existing active popups, accumulating overlapping tooltip boxes across the canvas.
- **Root Cause:** Lack of `popupRef` tracking to remove prior popups before instantiating a new one.

### Issue 4: Fragile Metric Formatting & Missing Defensive Fallbacks in `App.jsx`
- **Input:** Backend returns `null` or `undefined` for inspection metrics (e.g. `inspect_hs`, `wind_speed_kmh`, `current_speed_ms`, or `coordinates.latitude`) during network recovery or partial schema responses.
- **Expected:** UI gracefully formats missing values (e.g. `'—'`) without crashing.
- **Actual:** Unchecked calls to `safetyData.raw_metrics.wind_speed_kmh.toFixed(1)` and `safetyData.coordinates.latitude.toFixed(4)` threw unhandled `TypeError: Cannot read properties of undefined (reading 'toFixed')` crashing the entire React tree.
- **Root Cause:** Lack of optional chaining and defensive null checks on metric formatting.

### Issue 5: Non-Clickable Hour Step Pills on Forecast Timeline
- **Input:** User clicks directly on an hour badge (`00:00`, `03:00`, `06:00`, etc.) instead of dragging the slider thumb.
- **Expected:** Clicking the badge immediately updates `selectedHour` and triggers grid reloading.
- **Actual:** Hour pills were static `<span>` elements without `onClick` handlers or pointer cursors.
- **Root Cause:** Missing `onClick={() => setSelectedHour(h)}` on step pills in `App.jsx`.

---

## 2. What I Changed

1. **`frontend/src/components/MapContainer.jsx`**:
   - Added `onLocationSelect` to `mpa-fill` click listener to enable coordinate inspection and vessel marker positioning inside restricted sanctuaries.
   - Guarded `queryRenderedFeatures` with layer existence filter (`mapRef.current.getLayer(id)`) to prevent style errors on map clicks.
   - Added `popupRef` to clean up and replace popups cleanly without accumulating multiple tooltips.
   - Added `selectedDayRef` and `selectedHourRef` to guarantee fresh timeline arguments upon map style load.
   - Replaced duplicate SVG filter/gradient IDs (`boat-pin-shadow`, `boat-pin-gradient`) to prevent DOM ID collisions.

2. **`frontend/src/App.jsx`**:
   - Added defensive optional chaining and fallback formatting for all metric cards, coordinates, and wind/current direction metrics.
   - Added interactive `onClick` handlers and hover styling to timeline hour step badges.
   - Normalized wind direction degree calculation with modulo 360 arithmetic (`(inspect_mwd + 20) % 360`).
   - Hardened `DEFAULT_SAFETY_DATA` and `DEFAULT_FORECAST_TIMELINE` structures.

3. **Re-built Frontend Artifacts**:
   - Rebuilt production bundle via `npm run build` in `frontend/dist`.

---

## 3. Verification Record

### Unit & Integration Test Suites
- `PYTHONPATH=backend ./.venv/bin/python backend/tests/run_tests.py` -> 6/6 BSI Calculator unit tests passed.
- Complete API integration test suite covering:
  - `GET /` -> HTTP 200 (serves compiled SPA index).
  - `GET /assets/index-BcSQP8XR.js` -> HTTP 200 (compiled React JS bundle).
  - `GET /assets/index-D7D4jVWx.css` -> HTTP 200 (Tailwind CSS bundle).
  - `GET /api/health` -> HTTP 200 `{'status': 'ok'}`.
  - `GET /api/geofence/geojson` -> HTTP 200 (8 features: 2 EEZ + 6 MPAs).
  - `GET /api/geofence?lat=17.431&lon=84.703` -> HTTP 200 `SAFE_INSIDE_BORDER`.
  - `GET /api/geofence?lat=10.0&lon=60.0` -> HTTP 200 `DANGER_OUTSIDE_BORDER`.
  - `GET /api/geofence?lat=9.188&lon=78.918` -> HTTP 200 `DANGER_INSIDE_RESTRICTED_ZONE`.
  - `GET /api/safety?lat=17.431&lon=84.703&beam=3.5&day=1` -> HTTP 200.
  - `GET /api/safety/forecast?lat=17.431&lon=84.703&day=1` -> HTTP 200 (8 steps).
  - `GET /api/safety/grid?day=1&hour=12` -> HTTP 200 (995 coastal BSI cells).
  - `GET /api/safety/advisories` -> HTTP 200.
  - `GET /api/nonexistent` -> HTTP 404 JSON (does not serve SPA index for API routes).
  - `GET /some/spa/route` -> HTTP 200 HTML (proper SPA catch-all).
