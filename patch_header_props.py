with open("frontend/src/components/navigation/TopHeader.jsx", "r") as f:
    content = f.read()

old_sig = """export function TopHeader({
  activeMode = 'routing',
  selectedLocation = { lat: 17.431, lon: 84.703 },
  safetyData = null,
  dataStatus = {},
  isLoading = false,
  onRefresh,
  onBackToLanding,
  onToggleChat,
  isChatOpen = false
}) {"""

new_sig = """export function TopHeader({
  activeMode = 'routing',
  selectedLocation = { lat: 17.431, lon: 84.703 },
  safetyData = null,
  dataStatus = {},
  isLoading = false,
  onRefresh,
  onBackToLanding,
  onToggleChat,
  isChatOpen = false,
  currentTime = new Date().toISOString()
}) {"""

content = content.replace(old_sig, new_sig)

with open("frontend/src/components/navigation/TopHeader.jsx", "w") as f:
    f.write(content)
print("TopHeader props patched")
