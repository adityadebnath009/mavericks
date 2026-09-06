const fs = require('fs');

const path = 'frontend/src/components/sidebars/WeatherSidebar.jsx';
let content = fs.readFileSync(path, 'utf8');

// Replace old data extraction logic with new ORCA schema logic
content = content.replace(
  "const overallRisk = safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';",
  "const bsiScore = safetyData?.severity_score || 0;\n  const overallRisk = safetyData?.orca_risk?.rating || 'SAFE';"
);

content = content.replace(
  "const raw = safetyData?.raw_metrics || {};",
  "const raw = safetyData?.raw_metrics || {};\n  const availableHazards = safetyData?.available_hazards || [];\n  const unavailableHazards = safetyData?.unavailable_hazards || [];\n  const hazards = safetyData?.hazards || {};"
);

// We need to render the missing hazards in the UI
// Let's find the section that renders 'Meteorological Hazards' and inject the list of hazards
// Wait, I will write a simple sed or replacement to insert the hazard blocks.

fs.writeFileSync(path, content, 'utf8');
