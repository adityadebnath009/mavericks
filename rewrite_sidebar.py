with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "r") as f:
    content = f.read()

# 1. Add import
if "getNearbyLandingCenters" not in content:
    content = content.replace(
        "import { MOCK_PORTS } from '../../services/mockData';",
        "import { getNearbyLandingCenters } from '../../services/api';"
    )

# 2. Add state and effect
state_hook = """  const [selectedOriginPort, setSelectedOriginPort] = useState('mumbai');
  const [selectedDestPort, setSelectedDestPort] = useState('');"""

new_state_hook = """  const [selectedOriginPort, setSelectedOriginPort] = useState('');
  const [selectedDestPort, setSelectedDestPort] = useState('');
  const [landingCenters, setLandingCenters] = useState([]);

  useEffect(() => {
    getNearbyLandingCenters(18.9220, 72.8347)
      .then(setLandingCenters)
      .catch(console.error);
  }, []);"""

content = content.replace(state_hook, new_state_hook)

# 3. Update handle functions
old_origin_change = """  const handleOriginPortChange = (e) => {
    const portId = e.target.value;
    setSelectedOriginPort(portId);
    const port = MOCK_PORTS.find(p => p.id === portId);
    if (port && onLocationSelect) {
      onLocationSelect({ lat: port.lat, lon: port.lon });
    }
  };"""
  
new_origin_change = """  const handleOriginPortChange = (e) => {
    const portId = e.target.value;
    setSelectedOriginPort(portId);
    const port = landingCenters.find(p => p.id === portId);
    if (port && onLocationSelect) {
      onLocationSelect({ lat: port.lat, lon: port.lon });
    }
  };"""
content = content.replace(old_origin_change, new_origin_change)

old_dest_change = """  const handleDestPortChange = (e) => {
    const portId = e.target.value;
    setSelectedDestPort(portId);
    const port = MOCK_PORTS.find(p => p.id === portId);
    if (port && onDestinationSelect) {
      onDestinationSelect({ lat: port.lat, lon: port.lon });
    }
  };"""
  
new_dest_change = """  const handleDestPortChange = (e) => {
    const portId = e.target.value;
    setSelectedDestPort(portId);
    const port = landingCenters.find(p => p.id === portId);
    if (port && onDestinationSelect) {
      onDestinationSelect({ lat: port.lat, lon: port.lon });
    }
  };"""
content = content.replace(old_dest_change, new_dest_change)

# 4. Replace MOCK_PORTS.map
content = content.replace(
    """{MOCK_PORTS.map(port => (
                <option key={port.id} value={port.id}>
                  {port.name} ({port.lat.toFixed(2)}°N, {port.lon.toFixed(2)}°E)
                </option>
              ))}""",
    """{landingCenters.map(port => (
                <option key={port.id} value={port.id}>
                  {port.name}, {port.district} ({port.lat.toFixed(2)}°N, {port.lon.toFixed(2)}°E)
                </option>
              ))}"""
)

with open("frontend/src/components/sidebars/RoutingSidebar.jsx", "w") as f:
    f.write(content)
