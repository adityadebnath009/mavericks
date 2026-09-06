import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Make the heatmap radius super tight to prevent bleeding over the 27km buffer
old_radius = "'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 20, 10, 50],"
new_radius = "'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 12, 10, 35],"
content = content.replace(old_radius, new_radius)

# Update weight to map smoothly
old_weight = """            'heatmap-weight': [
              'interpolate',
              ['linear'],
              ['get', 'bsi'],
              0, 0.1,
              3, 0.4,
              7, 1.0
            ],"""
new_weight = """            'heatmap-weight': [
              'interpolate',
              ['linear'],
              ['get', 'severity'],
              0, 0.0,
              50, 0.5,
              100, 1.0
            ],"""
content = content.replace(old_weight, new_weight)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
