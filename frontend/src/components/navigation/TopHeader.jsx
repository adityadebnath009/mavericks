import React from 'react';
import { ArrowLeft, Waves, RefreshCw, Sparkles } from 'lucide-react';
import RiskBadge from '../common/RiskBadge';

const MODE_TITLES = {
  routing: { tag: 'TACTICAL ROUTING', desc: 'A* Safe Pathfinding & Boundary Geofencing' },
  fisheries: { tag: 'OCEAN ANALYTICS', desc: 'Potential Fishing Zones & Thermal Fronts' },
  weather: { tag: 'METEOROLOGICAL HAZARDS', desc: 'SVAS Capsizing BSI & Severe Weather' }
};

const STATUS_META = {
  loading: { label: 'LOADING', className: 'text-[#FFB547]', dot: 'bg-[#FFB547]' },
  live: { label: 'LIVE', className: 'text-[#18C7A0]', dot: 'bg-[#18C7A0]' },
  cached: { label: 'CACHED', className: 'text-[#FFB547]', dot: 'bg-[#FFB547]' },
  unavailable: { label: 'OFFLINE', className: 'text-[#FF5C5C]', dot: 'bg-[#FF5C5C]' }
};

function StatusBadge({ label, status, icon: Icon }) {
  const meta = STATUS_META[status] || STATUS_META.unavailable;
  return (
    <div className={`flex items-center gap-1.5 bg-[#13263A] border border-[#20384D] px-2 py-0.5 rounded ${meta.className}`}>
      {Icon ? <Icon className="w-3 h-3" /> : <div className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />}
      <span>{label}: {meta.label}</span>
    </div>
  );
}

export function TopHeader({
  activeMode = 'routing',
  selectedLocation = { lat: 17.431, lon: 84.703 },
  safetyData = null,
  dataStatus = {},
  isLoading = false,
  onRefresh,
  onBackToLanding,
  onToggleChat,
  isChatOpen = false
}) {
  const modeInfo = MODE_TITLES[activeMode] || MODE_TITLES.routing;
  const overallRisk = safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';
  const distToBorder = safetyData?.raw_metrics?.distance_to_border_km;

  return (
    <header className="h-12 min-h-[48px] border-b border-[#20384D] bg-[#0D1B2A] px-4 sm:px-6 flex items-center justify-between text-xs select-none z-20 shrink-0">
      <div className="flex items-center gap-3">
        {onBackToLanding && (
          <button onClick={onBackToLanding} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#13263A] hover:bg-[#1b344e] text-[#00D4FF] border border-[#20384D] hover:border-[#00D4FF]/40 transition-colors font-mono text-[10px] font-bold cursor-pointer" title="Return to Landing Page & Overview">
            <ArrowLeft className="w-3 h-3" />
            <span className="hidden md:inline">OVERVIEW</span>
          </button>
        )}
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-[#00D4FF] animate-pulse shadow-[0_0_8px_#00D4FF]" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-[#EAF4F8] uppercase tracking-widest text-xs font-mono">NAVIK // CONSOLE</span>
              <span className="hidden lg:inline text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-bold">[ {modeInfo.tag} ]</span>
            </div>
            <span className="text-[9px] text-[#8FA8B8] hidden sm:block">{modeInfo.desc}</span>
          </div>
        </div>
      </div>

      <div className="hidden md:flex items-center gap-4 font-mono text-[10px]">
        <div className="bg-[#07111F] px-3 py-1 rounded-lg border border-[#20384D] flex items-center gap-3 text-[#8FA8B8]">
          <div>
            <span className="text-[8px] text-[#8FA8B8] uppercase block">Position</span>
            <span className="text-[#EAF4F8] font-bold">
              {selectedLocation?.lat != null ? `${Number(selectedLocation.lat).toFixed(4)}°N` : '—'} • {selectedLocation?.lon != null ? `${Number(selectedLocation.lon).toFixed(4)}°E` : '—'}
            </span>
          </div>
          <div className="h-4 w-[1px] bg-[#20384D]" />
          <div>
            <span className="text-[8px] text-[#8FA8B8] uppercase block">Border Proximity</span>
            <span className="text-[#00D4FF] font-bold">{distToBorder != null ? `${Number(distToBorder).toFixed(1)} km` : 'EEZ CLEAR'}</span>
          </div>
        </div>
        <RiskBadge level={overallRisk} size="sm" />
      </div>

      <div className="flex items-center gap-4 text-[#8FA8B8] font-semibold">
        <div className="hidden xl:flex items-center gap-3 text-[10px] font-mono">
          <StatusBadge label="INCOIS" status={dataStatus.safety} />
          <StatusBadge label="WW3" status={dataStatus.vectors} icon={Waves} />
        </div>

        <div className="text-right hidden sm:block">
          <span className="text-[8px] text-[#8FA8B8] block uppercase font-mono">Forecast Epoch</span>
          <span className="font-mono text-[#EAF4F8] font-bold text-[10px]">{new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()} • {new Date().toISOString().substring(11, 16)} UTC</span>
        </div>

        <div className="flex items-center gap-2 border-l border-[#20384D] pl-3 sm:pl-4">
          {onRefresh && (
            <button onClick={onRefresh} disabled={isLoading} className="p-1.5 bg-[#13263A] hover:bg-[#1b344e] text-[#EAF4F8] rounded-lg border border-[#20384D] hover:border-[#00D4FF]/40 transition active:scale-95 cursor-pointer" title="Refresh Ocean Telemetry">
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-[#00D4FF]' : ''}`} />
            </button>
          )}
          {onToggleChat && (
            <button onClick={onToggleChat} className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border font-mono text-[10px] font-bold transition-all cursor-pointer ${isChatOpen ? 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0]' : 'bg-[#00D4FF]/10 hover:bg-[#00D4FF]/20 border-[#00D4FF]/40 text-[#00D4FF]'}`} title="Open AI Safety Advisor (Grounded RAG)">
              <Sparkles className="w-3 h-3" />
              <span className="hidden md:inline">ADVISOR</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default TopHeader;
