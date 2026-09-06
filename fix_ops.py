import re

with open("frontend/src/components/OperationsDashboard.jsx", "r") as f:
    content = f.read()

state_block = """  const [isChatOpen, setIsChatOpen] = useState(urlMode === 'advisor' || initialMode === 'advisor');
  const [routeError, setRouteError] = useState(null);"""

content = re.sub(r'  const \[isChatOpen, setIsChatOpen\] = useState\(urlMode === \'advisor\' \|\| initialMode === \'advisor\'\);', state_block, content)

with open("frontend/src/components/OperationsDashboard.jsx", "w") as f:
    f.write(content)

print("OperationsDashboard fixed")
