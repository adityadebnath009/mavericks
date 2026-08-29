import re
with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Add vectorGrid to props
old_props = """  gridGeojson = null,
  sstOpacity = 0.65,"""
new_props = """  gridGeojson = null,
  vectorGrid = { windGeojson: null, currentGeojson: null },
  sstOpacity = 0.65,"""
content = content.replace(old_props, new_props)

# Add map layers
old_layers_block = """        // --- 5. Source: incois-chl (Raster WMS) ---
        map.addSource('incois-chl', {
          type: 'raster',
          tiles: [
            'https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms?service=WMS&request=GetMap&layers=PFZ-TUNA-SST-CHL:chl&styles=&format=image/png&transparent=true&version=1.1.1&width=256&height=256&srs=EPSG:3857&bbox={bbox-epsg-3857}'
          ],
          tileSize: 256
        });

        // Layer 9: chl-raster
        map.addLayer({
          id: 'chl-raster',
          type: 'raster',
          source: 'incois-chl',
          paint: {
            'raster-opacity': chlOpacity
          },
          layout: { visibility: 'none' }
        });"""

new_layers_block = old_layers_block + """

        // --- 6. Source: vector-wind ---
        map.addSource('vector-wind', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });

        // Layer 10: wind-arrows
        map.addLayer({
          id: 'wind-arrows',
          type: 'symbol',
          source: 'vector-wind',
          layout: {
            'icon-image': 'arrow-icon',
            'icon-rotate': ['get', 'direction_deg'],
            'icon-rotation-alignment': 'map',
            'icon-allow-overlap': true,
            'icon-size': 0.6,
            visibility: 'none'
          },
          paint: {
            'icon-color': [
              'interpolate', ['linear'], ['get', 'speed_kmh'],
              0, '#00D4FF',
              20, '#18C7A0',
              40, '#FFB547',
              60, '#FF5C5C'
            ],
            'icon-halo-color': '#07111F',
            'icon-halo-width': 1
          }
        });

        // --- 7. Source: vector-current ---
        map.addSource('vector-current', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });

        // Layer 11: current-arrows
        map.addLayer({
          id: 'current-arrows',
          type: 'symbol',
          source: 'vector-current',
          layout: {
            'icon-image': 'arrow-icon',
            'icon-rotate': ['get', 'direction_deg'],
            'icon-rotation-alignment': 'map',
            'icon-allow-overlap': true,
            'icon-size': 0.6,
            visibility: 'none'
          },
          paint: {
            'icon-color': [
              'interpolate', ['linear'], ['get', 'speed_ms'],
              0, '#00D4FF',
              0.5, '#18C7A0',
              1.0, '#FFB547',
              1.5, '#FF5C5C'
            ],
            'icon-halo-color': '#07111F',
            'icon-halo-width': 1
          }
        });
"""
content = content.replace(old_layers_block, new_layers_block)

# Fix visibility logic in updateLayerVisibility
# For weather:
old_weather_vis = """      weather: {
        'bsi-grid-fill': layersOverride.bsiRisk !== false ? 'visible' : 'none',
        'bsi-heatmap': (layersOverride.bsiRisk !== false) || layersOverride.windSpeed || layersOverride.currentSpeed ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories !== false ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories !== false ? 'visible' : 'none',
        'sst-raster': layersOverride.sst ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none',
        'route-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none'
      },"""
new_weather_vis = """      weather: {
        'bsi-grid-fill': layersOverride.bsiRisk !== false ? 'visible' : 'none',
        'bsi-heatmap': 'none',
        'wind-arrows': layersOverride.windSpeed !== false ? 'visible' : 'none',
        'current-arrows': layersOverride.currentSpeed !== false ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories !== false ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories !== false ? 'visible' : 'none',
        'sst-raster': layersOverride.sst ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none',
        'route-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none'
      },"""
content = content.replace(old_weather_vis, new_weather_vis)

old_fisheries_vis = """      fisheries: {
        'sst-raster': layersOverride.sst !== false ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll !== false ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory !== false ? 'visible' : 'none',
        'route-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories ? 'visible' : 'none',
        'bsi-grid-fill': layersOverride.bsiRisk ? 'visible' : 'none',
        'bsi-heatmap': layersOverride.bsiRisk || layersOverride.windSpeed || layersOverride.currentSpeed ? 'visible' : 'none'
      }"""
new_fisheries_vis = """      fisheries: {
        'sst-raster': layersOverride.sst !== false ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll !== false ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory !== false ? 'visible' : 'none',
        'route-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories ? 'visible' : 'none',
        'bsi-grid-fill': layersOverride.bsiRisk ? 'visible' : 'none',
        'bsi-heatmap': 'none',
        'wind-arrows': layersOverride.windVectors ? 'visible' : 'none',
        'current-arrows': layersOverride.currentVectors ? 'visible' : 'none'
      }"""
content = content.replace(old_fisheries_vis, new_fisheries_vis)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
