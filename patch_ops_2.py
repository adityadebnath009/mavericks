with open("frontend/src/components/OperationsDashboard.jsx", "r") as f:
    content = f.read()

# Replace beamWidth in dependency arrays
content = content.replace(
    "[selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour]",
    "[selectedLocation.lat, selectedLocation.lon, vesselProfile.beam_m, selectedDay, selectedHour]"
)

# Replace beamWidth in liveContext
content = content.replace(
    "beam_width: `${beamWidth.toFixed(1)}m`,",
    "beam_width: `${(vesselProfile?.beam_m || 3.5).toFixed(1)}m`,"
)

with open("frontend/src/components/OperationsDashboard.jsx", "w") as f:
    f.write(content)
