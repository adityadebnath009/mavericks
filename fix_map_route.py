import re
import os

f = "frontend/src/components/map/MapConsole.jsx"
with open(f, 'r') as fh: c = fh.read()

# Replace routeData?.route_coords?.length with routeData?.path?.length
# And replace routeData.route_coords with routeData.path.map(n => [n.lon, n.lat])
# Let's just create a synthetic constant derived from routeData to make it easy.

patch = """
    // 3. React to Route Data Prop Updates
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    const routeCoords = routeData?.path?.map(n => [n.lon, n.lat]) || [];
    const straightCoords = routeCoords.length > 0 ? [routeCoords[0], routeCoords[routeCoords.length - 1]] : [];
    
    const routeGeo = routeCoords.length ? {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: routeCoords }
    } : EMPTY_FEATURE_COLLECTION;

    const straightGeo = straightCoords.length ? {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: straightCoords }
    } : EMPTY_FEATURE_COLLECTION;
"""
c = re.sub(r'// 3\. React to Route Data Prop Updates.*?\n    const straightGeo =.*?: EMPTY_FEATURE_COLLECTION;', patch.strip(), c, flags=re.DOTALL)

# In addSource for optimized-route and straight-route at initial load:
patch2 = """
        const routeCoords = routeData?.path?.map(n => [n.lon, n.lat]) || [];
        const straightCoords = routeCoords.length > 0 ? [routeCoords[0], routeCoords[routeCoords.length - 1]] : [];

        // --- 6. Source: optimized-route (A* Path Vector) ---
        map.addSource('optimized-route', {
          type: 'geojson',
          data: routeCoords.length ? {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: routeCoords }
          } : EMPTY_FEATURE_COLLECTION
        });
"""
c = re.sub(r'// --- 6\. Source: optimized-route \(A\* Path Vector\).*?: EMPTY_FEATURE_COLLECTION\n        \}\);', patch2.strip(), c, flags=re.DOTALL)

patch3 = """
        // --- 7. Source: straight-route (Direct Baseline Comparison) ---
        map.addSource('straight-route', {
          type: 'geojson',
          data: straightCoords.length ? {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: straightCoords }
          } : EMPTY_FEATURE_COLLECTION
        });
"""
c = re.sub(r'// --- 7\. Source: straight-route \(Direct Baseline Comparison\).*?: EMPTY_FEATURE_COLLECTION\n        \}\);', patch3.strip(), c, flags=re.DOTALL)

# And in modeVisibilityMap, check routeData?.path instead of routeData?.route_coords
c = c.replace('const hasRoute = Boolean(routeData?.route_coords?.length);', 'const hasRoute = Boolean(routeData?.path?.length);')
c = c.replace('routeData?.route_coords?.length', 'routeData?.path?.length')
c = c.replace('routeData.route_coords[routeData.route_coords.length - 1][0]', 'routeData.path[routeData.path.length - 1].lon')
c = c.replace('routeData.route_coords[routeData.route_coords.length - 1][1]', 'routeData.path[routeData.path.length - 1].lat')

with open(f, 'w') as fh: fh.write(c)

