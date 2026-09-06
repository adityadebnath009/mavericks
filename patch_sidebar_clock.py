with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "r") as f:
    content = f.read()

# Update signature
old_sig = """  departureTime = new Date().toISOString(),
  setDepartureTime,
  onCalculateRoute,"""
new_sig = """  departureTime = new Date().toISOString(),
  setDepartureTime,
  isDepartureManual = false,
  setIsDepartureManual,
  onCalculateRoute,"""
content = content.replace(old_sig, new_sig)

# Update Now button to clear manual override
old_now = """                  onClick={() => setDepartureTime && setDepartureTime(new Date().toISOString())} """
new_now = """                  onClick={() => {
                    if (setIsDepartureManual) setIsDepartureManual(false);
                    if (setDepartureTime) setDepartureTime(new Date().toISOString());
                  }} """
content = content.replace(old_now, new_now)

# Update onChange to set manual override
old_onchange = """                onChange={e => {
                  if (setDepartureTime) {
                    if (!e.target.value) {
                      setDepartureTime(null);
                    } else {
                      const d = new Date(e.target.value);
                      if (!isNaN(d.getTime())) {
                        setDepartureTime(d.toISOString());
                      }
                    }
                  }
                }}"""
new_onchange = """                onChange={e => {
                  if (setIsDepartureManual) setIsDepartureManual(true);
                  if (setDepartureTime) {
                    if (!e.target.value) {
                      setDepartureTime(null);
                    } else {
                      const d = new Date(e.target.value);
                      if (!isNaN(d.getTime())) {
                        setDepartureTime(d.toISOString());
                      }
                    }
                  }
                }}"""
content = content.replace(old_onchange, new_onchange)

with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "w") as f:
    f.write(content)
print("RoutingSidebar patched for manual sync")
