import re

with open("frontend/src/components/OperationsDashboard.jsx", "r") as f:
    content = f.read()

# Replace beamWidth state with vesselProfile and departureTime
content = content.replace(
    "  const [beamWidth, setBeamWidth] = useState(3.5);",
    "  const [vesselProfile, setVesselProfile] = useState({ length_m: 10.0, beam_m: 3.5, cruising_speed_kn: 10.0 });\n  const [departureTime, setDepartureTime] = useState(new Date().toISOString());"
)

# Replace beamWidth in useCallbacks
content = content.replace(
    "[selectedLocation, destinationLocation, beamWidth, selectedDay, selectedHour]",
    "[selectedLocation, destinationLocation, vesselProfile, departureTime, selectedDay, selectedHour]"
)

# Replace calculateRoute call
content = content.replace(
    "setRouteData(await calculateRoute(selectedLocation, destinationLocation, beamWidth, selectedDay, selectedHour));",
    "setRouteData(await calculateRoute(selectedLocation, destinationLocation, vesselProfile, departureTime));"
)

# Replace getSafety call (it needs beam, so we pass vesselProfile.beam_m)
content = content.replace(
    "resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour))",
    "resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, vesselProfile.beam_m, selectedDay, selectedHour))"
)

# Replace RoutingSidebar props
content = content.replace(
    "beamWidth={beamWidth} setBeamWidth={setBeamWidth}",
    "vesselProfile={vesselProfile} setVesselProfile={setVesselProfile} departureTime={departureTime} setDepartureTime={setDepartureTime}"
)

# Replace MapConsole props
content = content.replace(
    "beamWidth={beamWidth}",
    "beamWidth={vesselProfile.beam_m}"
)

with open("frontend/src/components/OperationsDashboard.jsx", "w") as f:
    f.write(content)
print("ops dashboard patched")
