import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

old_block = """      if (boatMarkerRef.current) {
        boatMarkerRef.current.setLngLat(coords);
      } else {"""

new_block = """      if (boatMarkerRef.current) {
        boatMarkerRef.current.setLngLat(coords);
        // Smoothly fly to the new location if the user selects a distant port
        if (mapLoaded && mapRef.current) {
           mapRef.current.easeTo({ center: coords, speed: 0.8, curve: 1 });
        }
      } else {"""

content = content.replace(old_block, new_block)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
