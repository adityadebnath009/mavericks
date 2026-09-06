with open("frontend/src/components/OperationsDashboard.jsx", "r") as f:
    content = f.read()

# 1. Add ticking state
# Find where departureTime is defined
old_state = "  const [departureTime, setDepartureTime] = useState(new Date().toISOString());"
new_state = """  const [currentTime, setCurrentTime] = useState(new Date().toISOString());
  const [departureTime, setDepartureTime] = useState(new Date().toISOString());
  const [isDepartureManual, setIsDepartureManual] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date().toISOString();
      setCurrentTime(now);
      if (!isDepartureManual) {
        setDepartureTime(now);
      }
    }, 1000); // Tick every second to keep the clock precisely aligned
    return () => clearInterval(timer);
  }, [isDepartureManual]);"""

content = content.replace(old_state, new_state)

# 2. Pass currentTime to TopHeader
old_header = "onToggleChat={() => setIsChatOpen(!isChatOpen)} isChatOpen={isChatOpen} />"
new_header = "onToggleChat={() => setIsChatOpen(!isChatOpen)} isChatOpen={isChatOpen} currentTime={currentTime} />"

content = content.replace(old_header, new_header)

# 3. Pass isDepartureManual and setIsDepartureManual to RoutingSidebar
old_routing = "vesselProfile={vesselProfile} setVesselProfile={setVesselProfile} departureTime={departureTime} setDepartureTime={setDepartureTime}"
new_routing = "vesselProfile={vesselProfile} setVesselProfile={setVesselProfile} departureTime={departureTime} setDepartureTime={setDepartureTime} isDepartureManual={isDepartureManual} setIsDepartureManual={setIsDepartureManual}"

content = content.replace(old_routing, new_routing)

with open("frontend/src/components/OperationsDashboard.jsx", "w") as f:
    f.write(content)
print("Ops Dashboard patched for real-time clock")
