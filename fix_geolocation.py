with open("frontend/src/components/OperationsDashboard.jsx", "r") as f:
    content = f.read()

geolocation_hook = """  // Geolocation: Auto-detect user's actual location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setSelectedLocation({ lat: position.coords.latitude, lon: position.coords.longitude });
        },
        (error) => {
          console.warn("Geolocation denied or failed. Defaulting to Mumbai.", error);
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    }
  }, []);
"""

# Insert it before the first useEffect
if "navigator.geolocation.getCurrentPosition" not in content:
    content = content.replace("  useEffect(() => {\n    if (urlMode === 'advisor')", geolocation_hook + "\n  useEffect(() => {\n    if (urlMode === 'advisor')")
    with open("frontend/src/components/OperationsDashboard.jsx", "w") as f:
        f.write(content)
