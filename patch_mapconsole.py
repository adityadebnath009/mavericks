with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

old_block = """  useEffect(() => {
    if (!mapLoaded || !mapRef.current || !routeData?.path) return;
    routeData.path.forEach(n => {
      mapRef.current.setFeatureState(
        { source: 'route-nodes', id: n.node_id },
        { selected: n.node_id === selectedNodeId }
      );
    });
  }, [selectedNodeId, mapLoaded, routeData]);"""

new_block = """  useEffect(() => {
    if (!mapLoaded || !mapRef.current || !routeData?.path) return;
    if (!mapRef.current.isStyleLoaded()) return;
    try {
      routeData.path.forEach(n => {
        mapRef.current.setFeatureState(
          { source: 'route-nodes', id: n.node_id },
          { selected: n.node_id === selectedNodeId }
        );
      });
    } catch (e) {
      console.warn('Map style not ready for setFeatureState', e);
    }
  }, [selectedNodeId, mapLoaded, routeData]);"""

content = content.replace(old_block, new_block)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
print("mapconsole patched")
