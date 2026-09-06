import re

with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Replace the mapping logic that assumes polygons
old_logic = """    if (gridGeojson) {
      setSourceDataSafe('bsi-grid', gridGeojson);

      // Dynamically extract the centers of every blocky polygon to feed the smooth Heatmap engine
      const pointsData = {
        type: 'FeatureCollection',
        features: (gridGeojson.features || []).map(f => {
          const cLat = f.properties.center_lat ?? f.geometry.coordinates[0][0][1];
          const cLon = f.properties.center_lon ?? f.geometry.coordinates[0][0][0];
          return {
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [cLon, cLat] },
            properties: f.properties
          };
        })
      };
      setSourceDataSafe('bsi-points', pointsData);
    }"""

new_logic = """    if (gridGeojson) {
      setSourceDataSafe('bsi-grid', gridGeojson);

      // The backend grid is now natively a dense 0.25 Point cloud, so we pipe it directly!
      // (This fixes the geometry.coordinates[0][0] crash since they are no longer polygons)
      setSourceDataSafe('bsi-points', gridGeojson);
    }"""

content = content.replace(old_logic, new_logic)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)

