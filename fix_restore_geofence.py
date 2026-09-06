import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

marker = "        // Layer 6: mpa-stroke"

restored_code = """        // --- 3. Source: geofencing-layers ---
        map.addSource('geofencing-layers', {
          type: 'geojson',
          data: geofenceGeojson || EMPTY_FEATURE_COLLECTION
        });

        // Layer 5: mpa-fill (Restricted Sanctuaries)
        map.addLayer({
          id: 'mpa-fill',
          type: 'fill',
          source: 'geofencing-layers',
          filter: ['==', ['get', 'type'], 'MPA'],
          paint: {
            'fill-color': '#a855f7',
            'fill-opacity': 0.20
          },
          layout: { visibility: 'visible' }
        });

        // Layer 6: mpa-stroke"""

content = content.replace(marker, restored_code)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
