import React, { useState } from 'react';
import { 
  Compass, 
  ChevronDown, 
  ChevronUp, 
  ShieldAlert, 
  Fish, 
  Wind, 
  Navigation, 
  Waves 
} from 'lucide-react';

/**
 * MapLegend - Context-aware floating HUD legend for Naval Operations Console.
 * Follows Frozen Navik Design System palette (#07111F, #0D1B2A, #13263A, #00D4FF, #18C7A0, #FFB547, #FF5C5C).
 */
export function MapLegend({
  activeMode = 'routing',
  className = '',
  positionClassName = 'top-4 left-4',
  simulationEnabled = false,
  isCollapsed: controlledCollapsed,
  onToggleCollapse
}) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;
  const toggleCollapse = onToggleCollapse || (() => setInternalCollapsed(prev => !prev));

  return (
    <div 
      className={`absolute ${positionClassName} z-10 select-none transition-all duration-300 ${className}`}
      aria-label="Tactical Map Legend"
    >
      <div className="bg-[#0D1B2A]/90 backdrop-blur-md border border-[#20384D] rounded-xl shadow-2xl p-3.5 w-64 text-[#EAF4F8] font-sans">
        {/* Legend Header with Collapse Toggle */}
        <div 
          onClick={toggleCollapse}
          className="flex items-center justify-between cursor-pointer border-b border-[#20384D] pb-2 mb-2.5 group"
        >
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-[#00D4FF]" />
            <span className="font-mono text-xs font-extrabold uppercase tracking-wider text-[#EAF4F8]">
              {activeMode === 'routing' && 'Tactical Routing'}
              {activeMode === 'fisheries' && 'Fisheries Analytics'}
              {activeMode === 'weather' && 'Hazard Symbology'}
            </span>
          </div>
          <button 
            type="button" 
            className="text-[#8FA8B8] group-hover:text-[#00D4FF] transition-colors p-0.5 rounded"
            aria-label={isCollapsed ? 'Expand Legend' : 'Collapse Legend'}
          >
            {isCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Legend Body */}
        {!isCollapsed && (
          <div className="space-y-3 text-[10px]">
            {/* 1. Universal Boundaries (Always shown) */}
            <div className="space-y-1.5">
              <span className="text-[9px] font-mono font-bold text-[#8FA8B8] uppercase block">
                Maritime Boundaries
              </span>
              <div className="flex items-center gap-2.5">
                <div className="w-5 h-0 border-t-2 border-dashed border-[#FF5C5C] shrink-0" />
                <span className="text-[#8FA8B8]">Indian EEZ / IMBL Border</span>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-3 rounded bg-[#a855f7]/25 border border-[#9333ea] border-dashed shrink-0" />
                <span className="text-[#8FA8B8]">Restricted Sanctuary (MPA)</span>
              </div>
            </div>

            {/* 2. Routing Mode Specifics */}
            {activeMode === 'routing' && (
              <div className="space-y-1.5 border-t border-[#20384D]/70 pt-2">
                <span className="text-[9px] font-mono font-bold text-[#8FA8B8] uppercase block">
                  A* Vector Trajectories
                </span>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-1 rounded-full bg-[#00D4FF] shadow-[0_0_6px_#00D4FF] shrink-0" />
                  <span className="text-[#EAF4F8] font-semibold">Optimal Safe Path</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-0 border-t border-dashed border-[#8FA8B8] shrink-0" />
                  <span className="text-[#8FA8B8]">Direct Baseline Comparison</span>
                </div>
                <div className="flex items-center gap-2.5 pt-0.5">
                  <div className="w-3.5 h-3.5 rounded-full bg-[#18C7A0]/20 border border-[#18C7A0] flex items-center justify-center shrink-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#18C7A0]" />
                  </div>
                  <span className="text-[#8FA8B8]">{simulationEnabled ? 'Demo Vessel (Draggable)' : 'Vessel Origin (Draggable)'}</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-3.5 h-3.5 rounded-full bg-white/20 border border-white flex items-center justify-center shrink-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-white" />
                  </div>
                  <span className="text-[#8FA8B8]">Destination Waypoint</span>
                </div>
              </div>
            )}

            {/* 3. Fisheries Mode Specifics */}
            {activeMode === 'fisheries' && (
              <div className="space-y-2 border-t border-[#20384D]/70 pt-2">
                <span className="text-[9px] font-mono font-bold text-[#8FA8B8] uppercase block">
                  Oceanic Layers & PFZ
                </span>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-1 rounded-full bg-[#FFB547] shadow-[0_0_6px_#FFB547] shrink-0" />
                  <span className="text-[#FFB547] font-bold">PFZ High Catch Vector</span>
                </div>
                
                {/* SST Colorbar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[8px] text-[#8FA8B8]">
                    <span>SST Heatmap</span>
                    <span>24°C — 32°C</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-gradient-to-r from-blue-600 via-emerald-400 to-rose-500" />
                </div>

                {/* Chlorophyll Colorbar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[8px] text-[#8FA8B8]">
                    <span>Chlorophyll-a</span>
                    <span>0.05 — 2.0 mg/m³</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-gradient-to-r from-teal-900 via-emerald-500 to-lime-300" />
                </div>
              </div>
            )}

            {/* 4. Weather Mode Specifics */}
            {activeMode === 'weather' && (
              <div className="space-y-2 border-t border-[#20384D]/70 pt-2">
                <span className="text-[9px] font-mono font-bold text-[#8FA8B8] uppercase block">
                  SVAS Capsizing BSI Risk Ramp
                </span>
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded bg-[#18C7A0]/30 border border-[#18C7A0]" />
                    <span className="text-[#18C7A0] font-semibold">SAFE (0-1)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded bg-[#EAB308]/30 border border-[#EAB308]" />
                    <span className="text-[#EAB308] font-semibold">CAUTION (2-3)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded bg-[#FFB547]/30 border border-[#FFB547]" />
                    <span className="text-[#FFB547] font-semibold">ALERT (4-5)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded bg-[#FF5C5C]/30 border border-[#FF5C5C]" />
                    <span className="text-[#FF5C5C] font-semibold">WARNING (6-7)</span>
                  </div>
                </div>

                <div className="pt-1">
                  <span className="text-[9px] font-mono font-bold text-[#8FA8B8] uppercase block mb-1">
                    INCOIS Coastal Advisories
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-[#FFB547]/20 border border-[#FFB547]" />
                    <span className="text-[#8FA8B8]">District Multi-Beam Advisory</span>
                  </div>
                </div>
              </div>
            )}

            {/* Informational Footer */}
            <div className="border-t border-[#20384D]/70 pt-2 text-[8px] text-[#8FA8B8] italic font-mono">
              {simulationEnabled ? 'Demo mode • Drag vessel or markers to update' : 'Left-click map to inspect • Drag markers to update'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MapLegend;
