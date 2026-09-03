with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "r") as f:
    content = f.read()

content = content.replace(
    "getNearbyLandingCenters(18.9220, 72.8347)",
    "getNearbyLandingCenters(selectedLocation.lat || 18.9220, selectedLocation.lon || 72.8347)"
)

content = content.replace("}, []);", "}, [selectedLocation.lat, selectedLocation.lon]);")

with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "w") as f:
    f.write(content)
