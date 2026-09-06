with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "r") as f:
    content = f.read()

old_input = """                onChange={e => {
                  if (e.target.value && setDepartureTime) {
                    const d = new Date(e.target.value);
                    if (!isNaN(d.getTime())) {
                      setDepartureTime(d.toISOString());
                    }
                  }
                }}"""

# If the user clears the input (or types an incomplete date), e.target.value is "".
# We must allow the state to become empty/null so the input clears.
new_input = """                onChange={e => {
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

content = content.replace(old_input, new_input)

with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "w") as f:
    f.write(content)
print("RoutingSidebar patched again")
