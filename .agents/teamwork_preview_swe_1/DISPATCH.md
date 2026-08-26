## 2026-08-26T13:44:02Z
Task:
Revert, stabilize, and verify the ORCA Marine Portal UI to fully restore the interactive map layers, coordinates inspection, sidebars, and bottom Recharts graphs.

Requirements:
1. UI Layout Restoral & Stabilization:
- Restore the sidebar panels, overall status banners, recommendations, ocean state inspection details, and data provenance blocks to a fully functioning state.
- Ensure that the page does not load in a blank or crashed state (e.g. if the backend database/APIs fallback or default, the UI must gracefully handle and render these values).
- Add responsive Recharts graphs in the bottom panel rendering 24-hour trends for BSI, wave height, wind speed, and current speed.
- Verify changing forecast day tabs or continuous beam width slider dynamically updates vessel profile class (<4m, <6m, <7m) and fetches new safety data.

2. Map Layers & Markings Restoral:
- Initialize the MapLibre GL map centered over the Indian peninsula and EEZ boundaries.
- Use a high-quality dark grey base tile server (e.g. Esri World Dark Gray Base) that is free and does not display watermarks like "API KEY REQUIRED".
- Restore all spatial markings: the red-dashed EEZ border line, purple-dashed Marine Protected Area (MPA) boundaries, and the dynamic grid of BSI risk cells (colored green, yellow, orange, red).
- Restore coordinates selection by clicking anywhere on the map grid or ocean waters, placing the custom boat marker and displaying inspection results in the sidebar.

Execute the SWE Light loop: dispatch the implementer, run review rounds, establish correctness through tests and verification, maintain progress in your working directory, and report completion back when ready.
