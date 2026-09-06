import re

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "r") as f:
    content = f.read()

old_func = """  const handleSetPfzDestination = (pfzFeature) => {
    if (!pfzFeature?.geometry?.coordinates?.length) return;
    const coords = pfzFeature.geometry.coordinates[0];
    if (onDestinationSelect) {
      onDestinationSelect({ lat: coords[1], lon: coords[0] });
    }
    if (onSelectPfz) {
      onSelectPfz(pfzFeature);
    }
  };"""

new_func = """  const handleSetPfzDestination = (pfzFeature) => {
    if (!pfzFeature?.geometry?.coordinates?.length) return;
    let coords = pfzFeature.geometry.coordinates[0];
    
    // Handle MultiLineString where coordinates[0] is an array of points
    while (Array.isArray(coords[0])) {
        coords = coords[0];
    }
    
    if (onDestinationSelect) {
      onDestinationSelect({ lat: coords[1], lon: coords[0] });
    }
    if (onSelectPfz) {
      onSelectPfz(pfzFeature);
    }
  };"""

content = content.replace(old_func, new_func)

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "w") as f:
    f.write(content)
