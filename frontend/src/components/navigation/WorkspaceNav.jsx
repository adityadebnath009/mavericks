import React from 'react';
import { 
  Navigation, 
  Fish, 
  Wind, 
  Bot, 
  Sparkles,
  ArrowLeft,
  Compass,
  Radio
} from 'lucide-react';

const WORKSPACE_ITEMS = [
  {
    id: 'routing',
    label: 'Tactical Routing',
    subLabel: 'A* Pathfinding & Risk HUD',
    shortcut: '01',
    icon: Navigation
  },
  {
    id: 'fisheries',
    label: 'Ocean Analytics',
    subLabel: 'PFZ Vectors & SST / CHL Heatmaps',
    shortcut: '02',
    icon: Fish
  },
  {
    id: 'weather',
    label: 'Meteorological Hazards',
    subLabel: 'SVAS BSI Capsizing & IMD Advisories',
    shortcut: '03',
    icon: Wind
  }
];

export function WorkspaceNav({
  activeMode = 'routing',
  setActiveMode,
  onToggleChat,
  isChatOpen = false,
  onBackToLanding
}) {
  return (
    <aside 
      className="w-16 min-w-[64px] h-full bg-[#0D1B2A] border-r border-[#20384D] flex flex-col items-center justify-between py-3.5 select-none z-30 shrink-0"
      aria-label="Workspace Navigation Rail"
    >
      {/* Top Section: Naval Radar Crest */}
      <div className="flex flex-col items-center gap-4 w-full">
        <button
          onClick={onBackToLanding}
          className="group relative flex items-center justify-center w-10 h-10 rounded-xl bg-[#13263A] border border-[#20384D] text-[#00D4FF] hover:border-[#00D4FF]/60 hover:shadow-[0_0_12px_rgba(0,212,255,0.25)] transition-all cursor-pointer"
          title="Return to System Overview"
        >
          <Compass className="w-5 h-5 group-hover:rotate-45 transition-transform duration-300" />
          
          {/* Tooltip */}
          <div className="absolute left-full ml-3 px-2.5 py-1 bg-[#13263A] border border-[#20384D] text-[#EAF4F8] text-[11px] rounded-lg shadow-xl font-mono whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-50">
            <span className="text-[#00D4FF] font-bold">NAVIK</span> // Overview
          </div>
        </button>

        <div className="w-8 h-[1px] bg-[#20384D]" />

        {/* Workspace Mode Switcher Buttons */}
        <nav className="flex flex-col items-center gap-2.5 w-full px-2" aria-label="Operational Workspaces">
          {WORKSPACE_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeMode === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActiveMode && setActiveMode(item.id)}
                className={`group relative flex items-center justify-center w-11 h-11 rounded-xl transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#00D4FF]/15 text-[#00D4FF] border border-[#00D4FF]/50 shadow-[0_0_15px_rgba(0,212,255,0.25)]'
                    : 'text-[#8FA8B8] hover:text-[#EAF4F8] hover:bg-[#13263A] border border-transparent hover:border-[#20384D]'
                }`}
                aria-current={isActive ? 'page' : undefined}
                aria-label={item.label}
              >
                {/* Active Left Indicator Bar */}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-[#00D4FF] rounded-r-full shadow-[0_0_8px_#00D4FF]" />
                )}

                <Icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${isActive ? 'stroke-[2.2]' : 'stroke-[1.8]'}`} />

                {/* Floating HUD Tooltip */}
                <div className="absolute left-full ml-3 px-3 py-1.5 bg-[#0D1B2A] border border-[#20384D] text-[#EAF4F8] rounded-lg shadow-2xl font-mono whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-all transform translate-x-1 group-hover:translate-x-0 z-50">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] text-[#00D4FF] font-bold bg-[#00D4FF]/10 px-1.5 py-0.5 rounded border border-[#00D4FF]/30">
                      {item.shortcut}
                    </span>
                    <span className="text-xs font-bold text-[#EAF4F8]">{item.label}</span>
                  </div>
                  <span className="text-[10px] text-[#8FA8B8] block mt-0.5">{item.subLabel}</span>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section: AI Safety Advisor & Live Status */}
      <div className="flex flex-col items-center gap-3 w-full px-2">
        <div className="w-8 h-[1px] bg-[#20384D]" />

        {/* AI Safety Advisor Button */}
        <button
          onClick={onToggleChat}
          className={`group relative flex items-center justify-center w-11 h-11 rounded-xl transition-all cursor-pointer ${
            isChatOpen
              ? 'bg-[#18C7A0]/20 text-[#18C7A0] border border-[#18C7A0]/60 shadow-[0_0_15px_rgba(24,199,160,0.3)]'
              : 'bg-[#13263A]/80 text-[#00D4FF] hover:bg-[#13263A] border border-[#20384D] hover:border-[#00D4FF]/40 hover:shadow-[0_0_10px_rgba(0,212,255,0.2)]'
          }`}
          aria-label="Toggle AI Safety Advisor"
        >
          {isChatOpen && (
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#18C7A0] animate-ping" />
          )}
          <Bot className="w-5 h-5 group-hover:scale-110 transition-transform" />

          {/* Floating Tooltip */}
          <div className="absolute left-full ml-3 px-3 py-1.5 bg-[#0D1B2A] border border-[#20384D] text-[#EAF4F8] rounded-lg shadow-2xl font-mono whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-all transform translate-x-1 group-hover:translate-x-0 z-50">
            <div className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-[#00D4FF]" />
              <span className="text-xs font-bold text-[#00D4FF]">AI Safety Advisor</span>
            </div>
            <span className="text-[10px] text-[#8FA8B8] block mt-0.5">Grounded RAG & Web Speech Voice</span>
          </div>
        </button>

        {/* Live Status Telemetry Dot */}
        <div 
          className="group relative flex items-center justify-center p-2 cursor-pointer"
          title="INCOIS Ocean State Telemetry: ONLINE"
        >
          <div className="w-2 h-2 rounded-full bg-[#18C7A0] animate-pulse shadow-[0_0_8px_#18C7A0]" />
          <div className="absolute left-full ml-3 px-2 py-1 bg-[#13263A] border border-[#20384D] text-[#18C7A0] text-[9px] font-mono font-bold rounded shadow-xl whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity z-50">
            SYSTEM ONLINE // 24H LIVE
          </div>
        </div>
      </div>
    </aside>
  );
}

export default WorkspaceNav;
