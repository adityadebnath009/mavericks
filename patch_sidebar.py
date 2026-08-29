import re
with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "r") as f:
    content = f.read()

# Replace handles
old_handles = """  const handleToggleWindHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      windSpeed: !prev.windSpeed,
      currentSpeed: false
    }));
  };

  const handleToggleCurrentHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      currentSpeed: !prev.currentSpeed,
      windSpeed: false
    }));
  };"""
new_handles = """  const handleToggleWindHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      windVectors: !prev.windVectors,
      currentVectors: false
    }));
  };

  const handleToggleCurrentHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      currentVectors: !prev.currentVectors,
      windVectors: false
    }));
  };"""
content = content.replace(old_handles, new_handles)

# Replace buttons
old_buttons = """          <div className="grid grid-cols-2 gap-2">
            {/* Wind Speed Heatmap Toggle */}
            <button
              type="button"
              onClick={handleToggleWindHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.windSpeed
                  ? 'bg-[#00D4FF]/20 border-[#00D4FF] text-[#00D4FF] shadow-[0_0_10px_rgba(0,212,255,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">Wind Heatmap</span>
                <Wind className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.windSpeed ? 'ACTIVE (km/h)' : 'OFF'}
              </span>
            </button>

            {/* Surface Current Heatmap Toggle */}
            <button
              type="button"
              onClick={handleToggleCurrentHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.currentSpeed
                  ? 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0] shadow-[0_0_10px_rgba(24,199,160,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">Current Heatmap</span>
                <Compass className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.currentSpeed ? 'ACTIVE (m/s)' : 'OFF'}
              </span>
            </button>
          </div>"""

new_buttons = """          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={handleToggleWindHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.windVectors
                  ? 'bg-[#00D4FF]/20 border-[#00D4FF] text-[#00D4FF] shadow-[0_0_10px_rgba(0,212,255,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">WIND VECTORS</span>
                <Wind className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.windVectors ? 'ACTIVE (km/h)' : 'OFF'}
              </span>
            </button>

            <button
              type="button"
              onClick={handleToggleCurrentHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.currentVectors
                  ? 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0] shadow-[0_0_10px_rgba(24,199,160,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">CURRENT VECTORS</span>
                <Compass className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.currentVectors ? 'ACTIVE (m/s)' : 'OFF'}
              </span>
            </button>
          </div>"""

content = content.replace(old_buttons, new_buttons)

with open("frontend/src/components/sidebars/FisheriesSidebar.jsx", "w") as f:
    f.write(content)
