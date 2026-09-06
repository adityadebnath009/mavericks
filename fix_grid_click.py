import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Replace bsi-grid-fill with an invisible circle layer for onClick events
old_fill = """        // Layer 1: bsi-grid-fill (Visible square cells)
        map.addLayer({
          id: 'bsi-grid-fill',
          type: 'fill',
          source: 'bsi-grid',
          paint: {
            'fill-color': ['get', 'color'],
            'fill-opacity': 0.5,
            'fill-outline-color': 'rgba(255,255,255,0.1)'
          },
          layout: { visibility: 'none' }
        });"""

new_fill = """        // Layer 1: bsi-grid-fill (Invisible points for clicking)
        map.addLayer({
          id: 'bsi-grid-fill',
          type: 'circle',
          source: 'bsi-grid',
          paint: {
            'circle-opacity': 0.0,
            'circle-radius': 10
          },
          layout: { visibility: 'none' }
        });"""

content = content.replace(old_fill, new_fill)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
