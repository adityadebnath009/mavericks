# Review Round 3 - Final Hardening & Verification Report

## Task Assessment
Reverted, stabilized, and verified the ORCA Marine Portal UI to fully restore the interactive map layers, coordinate inspection, sidebars, and bottom Recharts graphs.

## Issues Identified & Fixed in Round 3
1. **Generic Fallback Recommendations across Distinct Threat Types:**
   - **Input:** Vessel entered a Marine Protected Area (e.g. Gulf of Mannar) or crossed international EEZ borders into open international waters.
   - **Expected:** Tailored, actionable maritime advisories specific to the boundary breach (e.g., citing the specific sanctuary name or border crossing).
   - **Actual:** Backend returned generic 'Avoid the identified high-risk wave region' regardless of whether the hazard was a spatial violation, high winds, or wave forcing.
   - **Root Cause:** Single fallthrough recommendation string in backend/app/api/endpoints/safety.py. Fixed with context-specific recommendations for MPAs, EEZ borders, vessel beam instability, wave warnings, and extreme winds.

2. **Missing Explainability Citations in UI Recommendation Card:**
   - **Input:** User inspects a coordinate with compounding hazards (e.g., extreme wind speeds or vessel beam instability).
   - **Expected:** The recommendation card explicitly enumerates the underlying factors justifying the status rating in accordance with SIH explainability rules.
   - **Actual:** Only the primary summary recommendation was shown without the underlying bulleted reasons.
   - **Root Cause:** safetyData.reasons was ignored in frontend/src/App.jsx. Fixed by rendering the itemized reasons directly in the recommendation alert box.

3. **Vessel Sizing Vulnerability Feedback in Sidebar:**
   - **Input:** User drags the continuous beam width slider to a narrow width (< critical beam for prevailing waves).
   - **Expected:** Vessel profile card alerts the user with a dynamic Vulnerable status badge and critical beam threshold.
   - **Actual:** Status badge statically showed Active regardless of capsizing risk.
   - **Root Cause:** Missing conditional badge rendering based on safetyData.vessel_suitability.vulnerable in App.jsx.

4. **Recharts Y-Axis Tick Text Margin & Width Constraints:**
   - **Input:** Forecast timeline metrics with double/triple digit values (e.g. 40.4 km/h wind, 2.5 m wave height).
   - **Expected:** Y-axis numbers remain fully visible without clipping at small breakpoints.
   - **Actual:** Negative left margin -10 and narrow width 20 could clip digit labels on high-DPI displays.
   - **Root Cause:** Overly aggressive negative margin in BarChart and AreaChart components. Fixed with normalized margin.left = -2 and YAxis.width = 22..24.

5. **Initial Map View Framing:**
   - **Input:** Initial application page load.
   - **Expected:** Map remains centered over the Indian peninsula and EEZ boundaries at zoom 4.5.
   - **Actual:** Marker initialization triggered an immediate camera ease away from the national overview.
   - **Root Cause:** Missing initial mount guard on camera easing in MapContainer.jsx. Fixed with isInitialMountRef.

## Verification Record
- **Unit Tests:** PYTHONPATH=backend ./.venv/bin/python backend/tests/run_tests.py -> 6/6 tests passed.
- **Integration Tests:** Comprehensive suite covering:
  - Static asset serving (GET /, GET /assets/index-*.js, GET /assets/index-*.css) -> HTTP 200.
  - SPA client routing fallback (GET /dashboard/marine-risk) -> HTTP 200.
  - API isolation (GET /api/invalid_endpoint) -> HTTP 404.
  - Geofence status (SAFE_INSIDE_BORDER, DANGER_OUTSIDE_BORDER, DANGER_INSIDE_RESTRICTED_ZONE) -> HTTP 200.
  - Boundary GeoJSON (GET /api/geofence/geojson returning 8 features) -> HTTP 200.
  - Point safety assessment, forecast timeline, 2D BSI grid, and SVAS proxy -> HTTP 200.
- **Frontend Production Build:** npm --prefix frontend run build compiled cleanly via Vite in 4.59s.
