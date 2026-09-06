import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# 1. Change bsi-grid-fill opacity to rely on the severity color
old_fill = """        // Layer 1: bsi-grid-fill (Invisible but clickable)
        map.addLayer({
          id: 'bsi-grid-fill',
          type: 'fill',
          source: 'bsi-grid',
          paint: {
            'fill-opacity': 0.0 // Completely invisible, used only for onClick events
          },
          layout: { visibility: 'none' }
        });"""

new_fill = """        // Layer 1: bsi-grid-fill (Visible square cells)
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

content = content.replace(old_fill, new_fill)

# 2. Remove bsi-points and bsi-heatmap entirely
old_heatmap_pattern = r'// --- 1\.5\. Source: bsi-points.*?layout: \{ visibility: \'visible\' \}\n        \}, \'land\'\); // Place BELOW land layer so it doesn\'t overlap land'
content = re.sub(old_heatmap_pattern, '', content, flags=re.DOTALL)

# 3. Remove bsi-heatmap from layer toggles
content = content.replace("'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',", "")

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
