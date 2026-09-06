with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "r") as f:
    content = f.read()

# Fix the datetime-local value binding
old_input = """                value={departureTime ? new Date(departureTime).toISOString().slice(0, 16) : ''}
                onChange={e => setDepartureTime && setDepartureTime(new Date(e.target.value).toISOString())}"""

# We need to format the UTC departureTime into local time string for the input
new_input = """                value={departureTime ? (() => {
                  const d = new Date(departureTime);
                  if (isNaN(d.getTime())) return '';
                  const pad = n => n.toString().padStart(2, '0');
                  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
                })() : ''}
                onChange={e => {
                  if (e.target.value && setDepartureTime) {
                    const d = new Date(e.target.value);
                    if (!isNaN(d.getTime())) {
                      setDepartureTime(d.toISOString());
                    }
                  }
                }}"""

content = content.replace(old_input, new_input)

with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "w") as f:
    f.write(content)
print("RoutingSidebar patched")
