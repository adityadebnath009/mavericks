import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# routing
content = content.replace(
    "'bsi-heatmap': (layersOverride.bsiRisk !== false && activeMode === 'weather') || layersOverride.bsiRisk || layersOverride.windSpeed || layersOverride.currentSpeed ? 'visible' : 'none',",
    "'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',"
)

content = content.replace(
    "'bsi-heatmap': (layersOverride.bsiRisk !== false && activeMode === 'weather') || layersOverride.bsiRisk ? 'visible' : 'none',",
    "'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',"
)

# weather
content = content.replace(
    "'bsi-heatmap': layersOverride.bsiRisk !== false || layersOverride.windSpeed || layersOverride.currentSpeed ? 'visible' : 'none',",
    "'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',"
)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
