import re

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "r") as f:
    content = f.read()

# Replace the inner map block with {renderedPfzCards}
map_pattern = r'(\{pfzList\.map\(\(feat\) => \{.*?\)\;\s*\}\)\})'
match = re.search(map_pattern, content, flags=re.DOTALL)
if match:
    map_block = match.group(1)
    content = content.replace(map_block, "{renderedPfzCards}")

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "w") as f:
    f.write(content)
