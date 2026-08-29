import re
with open("frontend/src/components/OperationsDashboard.jsx", "r") as f:
    content = f.read()

# Add getVectorGrid to imports
content = content.replace("  getPfzLines,", "  getPfzLines,\n  getVectorGrid,")

# Add state variables
state_vars = """  const [pfzGeojson, setPfzGeojson] = useState(null);"""
new_state_vars = """  const [pfzGeojson, setPfzGeojson] = useState(null);
  const [vectorGrid, setVectorGrid] = useState({ windGeojson: null, currentGeojson: null });"""
content = content.replace(state_vars, new_state_vars)

# Fetch it
old_fetch = """        const [grid, adv, geo, pfz] = await Promise.all([
          getGrid(selectedDay, selectedHour),
          getAdvisories(),
          getGeofence(),
          getPfzLines()
        ]);

        if (isMounted) {
          if (grid) setGridGeojson(grid);
          if (adv) setAdvisoriesGeojson(adv);
          if (geo) setGeofenceGeojson(geo);
          if (pfz) setPfzGeojson(pfz);
        }"""
new_fetch = """        const [grid, adv, geo, pfz, vectors] = await Promise.all([
          getGrid(selectedDay, selectedHour),
          getAdvisories(),
          getGeofence(),
          getPfzLines(),
          getVectorGrid(selectedDay)
        ]);

        if (isMounted) {
          if (grid) setGridGeojson(grid);
          if (adv) setAdvisoriesGeojson(adv);
          if (geo) setGeofenceGeojson(geo);
          if (pfz) setPfzGeojson(pfz);
          if (vectors) setVectorGrid(vectors);
        }"""
content = content.replace(old_fetch, new_fetch)

# Pass it to MapConsole
old_map = """                pfzGeojson={pfzGeojson}
                advisoriesGeojson={advisoriesGeojson}
                geofenceGeojson={geofenceGeojson}
                gridGeojson={gridGeojson}
                sstOpacity={sstOpacity}"""
new_map = """                pfzGeojson={pfzGeojson}
                advisoriesGeojson={advisoriesGeojson}
                geofenceGeojson={geofenceGeojson}
                gridGeojson={gridGeojson}
                vectorGrid={vectorGrid}
                sstOpacity={sstOpacity}"""
content = content.replace(old_map, new_map)

with open("frontend/src/components/OperationsDashboard.jsx", "w") as f:
    f.write(content)
