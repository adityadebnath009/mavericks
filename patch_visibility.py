import re

with open('frontend/src/components/map/MapConsole.jsx', 'r') as f:
    content = f.read()

# I will just insert wind-arrows and current-arrows into each mode dictionary.

content = content.replace(
    "'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none'",
    "'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none',\n        'wind-arrows': layersOverride.windSpeed ? 'visible' : 'none',\n        'current-arrows': layersOverride.currentSpeed ? 'visible' : 'none'"
)

content = content.replace(
    "'advisory-stroke': layersOverride.advisories ? 'visible' : 'none'\n      },",
    "'advisory-stroke': layersOverride.advisories ? 'visible' : 'none',\n        'wind-arrows': layersOverride.windSpeed ? 'visible' : 'none',\n        'current-arrows': layersOverride.currentSpeed ? 'visible' : 'none'\n      },"
)

content = content.replace(
    "'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none'\n      }",
    "'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none',\n        'wind-arrows': layersOverride.windSpeed !== false ? 'visible' : 'none',\n        'current-arrows': layersOverride.currentSpeed !== false ? 'visible' : 'none'\n      }"
)

with open('frontend/src/components/map/MapConsole.jsx', 'w') as f:
    f.write(content)
