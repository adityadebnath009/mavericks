import re

with open("frontend/src/components/sidebars/WeatherSidebar.jsx", "r") as f:
    content = f.read()

handler_new = """
  const handleToggleCurrentHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      currentSpeed: !prev.currentSpeed,
      windSpeed: false
    }));
  };

  const handleToggleBsiHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      bsiRisk: !prev.bsiRisk
    }));
  };
"""

content = content.replace("""
  const handleToggleCurrentHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      currentSpeed: !prev.currentSpeed,
      windSpeed: false
    }));
  };
""", handler_new)

grid_new = """          <div className="grid grid-cols-3 gap-2">
            {/* Wind Vector Toggle */}
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
                <span className="text-[8px] font-mono uppercase font-bold">WIND VECTORS</span>
                <Wind className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.windSpeed ? 'ACTIVE' : 'OFF'}
              </span>
            </button>

            {/* Surface CURRENT VECTORS Toggle */}
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
                <span className="text-[8px] font-mono uppercase font-bold">CURRENTS</span>
                <Compass className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.currentSpeed ? 'ACTIVE' : 'OFF'}
              </span>
            </button>
            
            {/* BSI Heatmap Toggle */}
            <button
              type="button"
              onClick={handleToggleBsiHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.bsiRisk
                  ? 'bg-[#FF5C5C]/20 border-[#FF5C5C] text-[#FF5C5C] shadow-[0_0_10px_rgba(255,92,92,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">BSI HEATMAP</span>
                <AlertTriangle className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.bsiRisk ? 'ACTIVE' : 'OFF'}
              </span>
            </button>
          </div>
"""

old_grid_pattern = r'<div className="grid grid-cols-2 gap-2">.*?</span>\s*</button>\s*</div>'
content = re.sub(old_grid_pattern, grid_new, content, flags=re.DOTALL)

with open("frontend/src/components/sidebars/WeatherSidebar.jsx", "w") as f:
    f.write(content)
