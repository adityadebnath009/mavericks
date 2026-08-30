with open("frontend/src/components/sidebars/WeatherSidebar.jsx", "r") as f:
    content = f.read()

# Replace windSpeed with windVectors
content = content.replace("windSpeed: !prev.windSpeed,", "windVectors: !prev.windVectors,")
content = content.replace("windSpeed: false", "windVectors: false")
content = content.replace("layersOverride.windSpeed", "layersOverride.windVectors")

# Replace currentSpeed with currentVectors
content = content.replace("currentSpeed: !prev.currentSpeed,", "currentVectors: !prev.currentVectors,")
content = content.replace("currentSpeed: false", "currentVectors: false")
content = content.replace("layersOverride.currentSpeed", "layersOverride.currentVectors")

with open("frontend/src/components/sidebars/WeatherSidebar.jsx", "w") as f:
    f.write(content)
