import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Replace bsi-heatmap with blurred circles
old_heatmap_pattern = r"// Layer 2: bsi-heatmap \(Beautiful smooth gradient\).*?layout: \{ visibility: 'visible' \}\n        \}\);"
new_heatmap = """// Layer 2: bsi-heatmap (Data-driven blurred circles)
        map.addLayer({
          id: 'bsi-heatmap',
          type: 'circle',
          source: 'bsi-points',
          paint: {
            'circle-color': [
              'interpolate',
              ['linear'],
              ['get', 'severity'],
              0, '#18C7A0',  // Safe (Green)
              40, '#18C7A0', // Stay green longer
              50, '#FFB547', // Moderate (Yellow)
              70, '#FF5C5C', // High (Red)
              100, '#FF5C5C' // Extreme (Red)
            ],
            // Scale radius up as you zoom in to keep the screen covered in color
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 0, 15, 6, 25, 10, 60],
            // Apply maximum blur so individual circles completely blend together
            'circle-blur': 1.0,
            'circle-opacity': 0.65,
            'circle-stroke-width': 0
          },
          layout: { visibility: 'visible' }
        });"""

content = re.sub(old_heatmap_pattern, new_heatmap, content, flags=re.DOTALL)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
