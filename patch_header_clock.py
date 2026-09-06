with open("frontend/src/components/navigation/TopHeader.jsx", "r") as f:
    content = f.read()

# Update signature
old_sig = "export default function TopHeader({ activeMode, selectedLocation, safetyData, dataStatus, isLoading, onRefresh, onBackToLanding, onToggleChat, isChatOpen }) {"
new_sig = "export default function TopHeader({ activeMode, selectedLocation, safetyData, dataStatus, isLoading, onRefresh, onBackToLanding, onToggleChat, isChatOpen, currentTime = new Date().toISOString() }) {"
content = content.replace(old_sig, new_sig)

# Update the rendered time string
old_time = "        <div className=\"text-right hidden sm:block\">\n          <span className=\"text-[8px] text-[#8FA8B8] block uppercase font-mono\">Forecast Epoch</span>\n          <span className=\"font-mono text-[#EAF4F8] font-bold text-[10px]\">{new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()} • {new Date().toISOString().substring(11, 16)} UTC</span>\n        </div>"

new_time = """        <div className="text-right hidden sm:block">
          <span className="text-[8px] text-[#8FA8B8] block uppercase font-mono">System Epoch</span>
          <span className="font-mono text-[#EAF4F8] font-bold text-[10px]">{new Date(currentTime).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()} • {new Date(currentTime).toISOString().substring(11, 16)} UTC</span>
        </div>"""

content = content.replace(old_time, new_time)

with open("frontend/src/components/navigation/TopHeader.jsx", "w") as f:
    f.write(content)
print("TopHeader patched")
