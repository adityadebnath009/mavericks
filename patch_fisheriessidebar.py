import re

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "r") as f:
    content = f.read()

# Extract the map block exactly
map_pattern = r'(\{pfzList\.map\(\(feat\) => \{.*?\)\;\s*\}\)\})'
match = re.search(map_pattern, content, flags=re.DOTALL)
if match:
    map_block = match.group(1)
    
    inner_map = map_block[1:-1].strip()
    
    memo_hook = f"""
  const renderedPfzCards = useMemo(() => {{
    return {inner_map};
  }}, [pfzList, selectedPfz, onSelectPfz, onDestinationSelect]);
"""
    
    content = content.replace(
        '  return (\n    <aside className="w-full h-full flex flex-col',
        memo_hook + '\n  return (\n    <aside className="w-full h-full flex flex-col'
    )
    
    content = content.replace(map_block, "{renderedPfzCards}")

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "w") as f:
    f.write(content)
