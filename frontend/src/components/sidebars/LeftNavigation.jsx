import React from 'react';

const LeftNavigation = ({ history = null, onQuerySelect, agentState = 'idle' }) => {
  // Retained as a compatibility fallback for callers outside IntelligenceConsole.
  // The Intelligence Console passes real local query history instead.
  const recentQueries = [
    "Nearest PFZ",
    "Sea safety tomorrow",
    "Safest route"
  ];

  const savedWorkspaces = [
    "Fishing Route A",
    "Bay of Bengal Study",
    "Paradip Operations"
  ];
  const hasLiveHistory = Array.isArray(history);
  const visibleQueries = hasLiveHistory ? history : recentQueries.map((query) => ({ id: query, query }));

  return (
    <div className="flex flex-col bg-transparent w-full h-full text-[#EAF4F8]">
      
      {/* Header */}
      <div className="p-4 border-b border-[#20384D] flex items-center space-x-2">
        <div className="w-6 h-6 bg-[#00D4FF] rounded flex items-center justify-center font-bold text-[#07111F] text-xs">
          O
        </div>
        <span className="font-bold tracking-widest text-sm uppercase">ORCA Console</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-8">
        
        {/* Recent Queries */}
        <div>
          <h2 className="text-[#8FA8B8] text-[10px] uppercase font-bold tracking-widest mb-3 flex items-center">
            <svg className="w-3 h-3 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            Recent Queries
          </h2>
          <ul className="space-y-1 relative before:absolute before:inset-y-0 before:left-[5px] before:w-[1px] before:bg-[#20384D]">
            {visibleQueries.map((entry, idx) => (
              <li key={entry.id || idx} className="relative pl-5 py-1 text-xs text-[#EAF4F8] hover:text-[#00D4FF] cursor-pointer group flex items-center">
                <span className="absolute left-0 w-2 h-[1px] bg-[#20384D] group-hover:bg-[#00D4FF] transition-colors"></span>
                <button type="button" onClick={() => onQuerySelect?.(entry)} className="min-w-0 truncate text-left">
                  <span className="block truncate">{entry.query || entry}</span>
                  {entry.state && <span className="block pt-0.5 text-[9px] font-mono uppercase text-[#8FA8B8]">{entry.state}{entry.createdAt ? ` · ${new Date(entry.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : ''}</span>}
                </button>
              </li>
            ))}
            {hasLiveHistory && visibleQueries.length === 0 && <li className="pl-5 py-1 text-xs italic text-[#8FA8B8]">Your submitted queries will appear here.</li>}
          </ul>
        </div>

        {/* Saved Workspaces */}
        <div>
          <h2 className="text-[#8FA8B8] text-[10px] uppercase font-bold tracking-widest mb-3 flex items-center">
            <svg className="w-3 h-3 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>
            Saved
          </h2>
          <ul className="space-y-1 relative before:absolute before:inset-y-0 before:left-[5px] before:w-[1px] before:bg-[#20384D]">
            {savedWorkspaces.map((workspace, idx) => (
              <li key={idx} className="relative pl-5 py-1 text-xs text-[#EAF4F8] hover:text-[#18C7A0] cursor-pointer group flex items-center">
                <span className="absolute left-0 w-2 h-[1px] bg-[#20384D] group-hover:bg-[#18C7A0] transition-colors"></span>
                <span className="truncate">{workspace}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Connection Status */}
      <div className="p-4 border-t border-[#20384D] bg-[#07111F]">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-[#18C7A0] animate-pulse"></div>
          <span className="text-[#8FA8B8] text-[10px] uppercase font-mono tracking-wider">{agentState === 'executing' ? 'Agents running' : 'Agents online'}</span>
        </div>
      </div>

    </div>
  );
};

export default LeftNavigation;
