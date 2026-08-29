import re
with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Add SVG Arrow creation and updating logic
icon_logic = """
        // 0. Base map logic
        map.on('load', () => {
          setMapLoaded(true);
          
          // Generate an Arrow SVG and add to map
          const arrowSvg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="19" x2="12" y2="5"></line>
              <polyline points="5 12 12 5 19 12"></polyline>
            </svg>
          `;
          const img = new Image();
          img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(arrowSvg);
          img.onload = () => {
            if (!map.hasImage('arrow-icon')) {
              map.addImage('arrow-icon', img, { sdf: true });
            }
          };
"""

content = content.replace("        map.on('load', () => {\n          setMapLoaded(true);", icon_logic)

# Update vector source logic
update_logic = """
  useEffect(() => {
    if (mapRef.current && mapLoaded && gridGeojson) {
      const src = mapRef.current.getSource('bsi-grid');
      if (src) src.setData(gridGeojson);
    }
  }, [gridGeojson, mapLoaded]);
"""

new_update_logic = update_logic + """
  useEffect(() => {
    if (mapRef.current && mapLoaded && vectorGrid) {
      const windSrc = mapRef.current.getSource('vector-wind');
      if (windSrc && vectorGrid.windGeojson) windSrc.setData(vectorGrid.windGeojson);
      
      const currSrc = mapRef.current.getSource('vector-current');
      if (currSrc && vectorGrid.currentGeojson) currSrc.setData(vectorGrid.currentGeojson);
    }
  }, [vectorGrid, mapLoaded]);
"""
content = content.replace(update_logic, new_update_logic)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
