const res = {marine_severity_score: 58.0, fishing_opportunity_score: null, sst_c: 29.8, chl_mg_m3: null};
const safetyScore = res?.marine_severity_score;
const fishingScore = res?.fishing_opportunity_score;
const fishText = fishingScore !== null ? `<span class="text-[#18C7A0] font-bold">Opportunity: ${fishingScore.toFixed(0)}/100</span>` : `<span class="text-[#8FA8B8]">No PFZ Match</span>`;
const sstVal = res.sst_c !== undefined && res.sst_c !== null ? `${res.sst_c.toFixed(1)}°C` : 'N/A';
const chlVal = res.chl_mg_m3 !== undefined && res.chl_mg_m3 !== null ? `${res.chl_mg_m3.toFixed(2)} mg/m³` : 'N/A';
console.log(sstVal, chlVal);
