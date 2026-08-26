# Dispatch Log

## 2026-08-26T14:00:19Z

Task summary:
Revert, stabilize, and verify the ORCA Marine Portal UI to fully restore the interactive map layers, coordinates inspection, sidebars, and bottom Recharts graphs.

Authoritative Request File: /Users/adityadebnath/Projects/mavericks/.agents/ORIGINAL_REQUEST.md

Key Requirements:
1. R1. UI Layout Restoral & Stabilization:
   - Restore sidebar panels, overall status banners, recommendations, ocean state inspection details, data provenance blocks.
   - Ensure the page does not load blank/crashed; handle fallback/default gracefully.
   - Add responsive Recharts graphs in bottom panel rendering 24-hour trends for BSI, wave height, wind speed, current speed.
2. R2. Map Layers & Markings Restoral (OpenStreetMap):
   - MapLibre GL map centered over Indian peninsula & EEZ boundaries.
   - Map Style: Standard public OpenStreetMap (OSM) raster tiles ('https://a.tile.openstreetmap.org/{z}/{x}/{y}.png') with detailed map detail and no watermarks.
   - Geofencing overlays: Red-dashed EEZ border line, purple-dashed Marine Protected Area (MPA) boundaries, dynamic grid of BSI risk cells.
   - Offline fallback: If remote PostGIS is unreachable, backend `/api/geofence/geojson` must fallback to reading/parsing/returning `data/boundaries/boundaries_fallback.geojson`.
   - Grid clicking: Restore coordinate selection by clicking anywhere on map grid or ocean waters.
