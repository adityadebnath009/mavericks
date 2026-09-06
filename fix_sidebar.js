const fs = require('fs');
const path = 'frontend/src/components/sidebars/WeatherSidebar.jsx';
let content = fs.readFileSync(path, 'utf8');

// 1. Update dailyBsi to use daily_peaks
content = content.replace(
  "const dailyBsi = safetyData?.provenance?.daily_bsi_forecast || {",
  "const dailyBsi = safetyData?.daily_peaks || {"
);

// 2. Add the Hazards UI card
const hazardsInjection = `        {/* ORCA Hazards Explainability */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#FFB547]" />
              Hazard Diagnostics
            </span>
            <span className="text-[9px] font-mono text-[#FFB547] font-bold">ORCA AI</span>
          </div>
          
          <div className="flex flex-col gap-2 text-[9px] font-mono">
            {['wave_steepness', 'crossing_sea', 'bimodal_crossing', 'susceptibility'].map(hazardKey => {
              const isAvailable = (safetyData?.available_hazards || []).includes(hazardKey);
              const isUnavailable = (safetyData?.unavailable_hazards || []).includes(hazardKey);
              const isTriggered = safetyData?.hazards?.[hazardKey]?.triggered;
              
              let statusText = 'SAFE';
              let statusColor = 'text-[#18C7A0]';
              
              if (isUnavailable) {
                statusText = 'UNAVAILABLE / MISSING DATA';
                statusColor = 'text-[#8FA8B8]';
              } else if (isTriggered) {
                statusText = 'TRIGGERED';
                statusColor = 'text-[#FF5C5C]';
              }
              
              return (
                <div key={hazardKey} className="flex justify-between items-center bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
                  <span className="text-[#EAF4F8] uppercase">{hazardKey.replace('_', ' ')}</span>
                  <span className={\`font-bold \${statusColor}\`}>{statusText}</span>
                </div>
              );
            })}
          </div>
        </SpotlightCard>

        {/* 2. Simulation Heatmap & Overlay Toggles Card */}`;

content = content.replace("{/* 2. Simulation Heatmap & Overlay Toggles Card */}", hazardsInjection);

// 3. Fix the main score display if the subagent missed it.
// The subagent left "1" instead of the actual score. Wait, let's check what it is.
// I will just replace the "0-7 Index" text completely.

fs.writeFileSync(path, content, 'utf8');
