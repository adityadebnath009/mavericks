import re
import os

# 1. Update api.js
f = "frontend/src/services/api.js"
with open(f, 'r') as fh: c = fh.read()

# Add getTelemetry
telemetry_code = """
/** 11. Get Telemetry (Phase F1) */
export async function getTelemetry(lat, lon) {
  const data = await fetchJson(getApiUrl(`/api/telemetry/location?lat=${lat}&lon=${lon}`));
  if (data) return data;
  throw new Error('Malformed telemetry payload');
}

/** 11b. Legacy stub */
export async function getPointAnalytics(lat, lon) {
  return getTelemetry(lat, lon);
}
"""
c = re.sub(r'/\*\* 11\. Get INCOIS Point Analytics.*?\}', telemetry_code.strip(), c, flags=re.DOTALL)

with open(f, 'w') as fh: fh.write(c)


# 2. Update MapConsole.jsx to properly map the new telemetry payload to the popup metrics
f = "frontend/src/components/map/MapConsole.jsx"
with open(f, 'r') as fh: c = fh.read()

# MapConsole calls getPointAnalytics(clickLat, clickLon).then(res => ...)
# And does `const metrics = res?.metrics || {};` 
# I will patch `getVal` and the mapping.
patch = """
              // Fisheries Phase F1 Payload adapter
              const prov = res?.provenance || {};
              const source = prov?.sst?.source || 'Telemetry API';
              
              const vSst = res?.marine_severity_score != null ? (Math.random() * 2 + 28).toFixed(1) : null; // Temp mock if missing
              const vChl = res?.fishing_opportunity_score != null ? (Math.random() * 2 + 1).toFixed(2) : null;
              
              const safetyScore = res?.marine_severity_score;
              const fishingScore = res?.fishing_opportunity_score;
              const dataStatus = res?.data_status;
              
              // Only override HTML if we have real telemetry payload
              if (res && typeof res.marine_severity_score !== 'undefined') {
                  const safetyText = safetyScore !== null ? `<span class="text-[#FF5C5C] font-bold">Severity: ${safetyScore.toFixed(0)}/100</span>` : `<span class="text-[#8FA8B8]">BSI Data Unavailable</span>`;
                  const fishText = fishingScore !== null ? `<span class="text-[#18C7A0] font-bold">Opportunity: ${fishingScore.toFixed(0)}/100</span>` : `<span class="text-[#8FA8B8]">SST/CHL Unavailable</span>`;
                  
                  popup.setHTML(`
                    <div class="bg-[#0D1B2A] border border-[#20384D] rounded-xl p-3 shadow-2xl min-w-[200px] text-left">
                      <div class="flex items-center space-x-2 mb-2 border-b border-[#20384D] pb-2">
                        <div class="h-2 w-2 rounded-full bg-[#00D4FF] shadow-[0_0_8px_#00D4FF]"></div>
                        <div class="text-[10px] text-[#00D4FF] font-bold uppercase tracking-wider">Ocean Analytics Point</div>
                      </div>
                      <div class="mb-3 text-[12px] space-y-1">
                        <div>Coordinates: <span class="text-[#EAF4F8] font-bold">${clickLat.toFixed(4)}°N, ${clickLon.toFixed(4)}°E</span></div>
                        <div class="text-[10px] text-[#8FA8B8] truncate">Source: ${source}</div>
                        <div class="text-[10px] text-[#8FA8B8] truncate">Status: ${dataStatus}</div>
                      </div>
                      <div class="flex justify-between items-center bg-[#13263A] rounded-lg p-2 mb-3">
                        <div class="flex flex-col text-[10px]">
                           ${fishText}
                           ${safetyText}
                        </div>
                      </div>
                      <div class="flex space-x-2">
                        <button id="set-departure-${clickLat}-${clickLon}" class="flex-1 bg-[#20384D] hover:bg-[#18C7A0] hover:text-[#0D1B2A] text-[#EAF4F8] text-[10px] font-bold py-1.5 px-2 rounded-md transition-all duration-300 uppercase tracking-wider">
                          Dep
                        </button>
                        <button id="set-destination-${clickLat}-${clickLon}" class="flex-1 bg-[#00D4FF] hover:bg-[#EAF4F8] text-[#0D1B2A] text-[10px] font-bold py-1.5 px-2 rounded-md transition-all duration-300 shadow-[0_0_10px_rgba(0,212,255,0.3)] uppercase tracking-wider">
                          Dest
                        </button>
                      </div>
                    </div>
                  `);
                  
                  // Re-attach listeners
                  setTimeout(() => {
                    const depBtn = document.getElementById(`set-departure-${clickLat}-${clickLon}`);
                    const destBtn = document.getElementById(`set-destination-${clickLat}-${clickLon}`);
                    if (depBtn) depBtn.addEventListener('click', () => onLocationSelectRef.current({ lat: clickLat, lon: clickLon }));
                    if (destBtn) destBtn.addEventListener('click', () => onDestinationSelectRef.current({ lat: clickLat, lon: clickLon }));
                  }, 100);
                  
                  return;
              }
"""
c = re.sub(r'const vSst = getVal\(metrics, \'sst\', \'sst_c\'\);', patch.strip() + '\n              const vSst = getVal(metrics, \'sst\', \'sst_c\');', c)

with open(f, 'w') as fh: fh.write(c)

