import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Replace windSpeed and currentSpeed with windVectors and currentVectors
content = content.replace("layersOverride.windSpeed", "layersOverride.windVectors")
content = content.replace("layersOverride.currentSpeed", "layersOverride.currentVectors")

# Find and delete the fallback fetch block
fallback_pattern = r'// Fetch Initial Fallbacks if props were null.*?// Map click handler'
# We have to be careful with regex, let's just do a manual exact replacement if we can find it.
