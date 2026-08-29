import re
with open("frontend/src/components/sidebars/WeatherSidebar.jsx", "r") as f:
    content = f.read()

content = content.replace("Wind Heatmap", "WIND VECTORS")
content = content.replace("Current Heatmap", "CURRENT VECTORS")

with open("frontend/src/components/sidebars/WeatherSidebar.jsx", "w") as f:
    f.write(content)
