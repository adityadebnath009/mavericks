import React, { useState } from 'react';
import LeftNavigation from '../components/sidebars/LeftNavigation';
import EvidenceLedger from '../components/sidebars/EvidenceLedger';
import CommandBar from '../components/chat/CommandBar';
import BriefingCard from '../components/chat/BriefingCard';
import OrchestrationHUD from '../components/timeline/OrchestrationHUD';
import MarineMap from '../components/map/MarineMap';

const IntelligenceConsole = () => {
  // STRICT RULE: ZERO HARDCODING. Initial state is empty.
  const [isProcessing, setIsProcessing] = useState(false);
  const [hudEvents, setHudEvents] = useState([]);
  const [currentPayload, setCurrentPayload] = useState(null);

  // This handles both text input AND follow-up button clicks
  const handleQuerySubmit = (query, language) => {
    // 1. Enter Loading / Orchestration State
    setIsProcessing(true);
    setCurrentPayload(null); // Clear previous UI
    
    // Simulate DAG Execution Trace
    setHudEvents([{ status: 'done', text: 'Query classified' }, { status: 'pending', text: 'Routing to Ocean Analytics...' }]);
    
    setTimeout(() => {
      setHudEvents(prev => [...prev.slice(0, 1), { status: 'done', text: 'Routing to Ocean Analytics...' }, { status: 'pending', text: 'Fetching GEE overlays...' }]);
    }, 800);

    setTimeout(() => {
      setHudEvents(prev => [...prev.slice(0, 2), { status: 'done', text: 'Fetching GEE overlays...' }, { status: 'pending', text: 'Validating evidence contract...' }]);
    }, 1600);

    // 2. Resolve Mock Payload (In production, this is the FastAPI response)
    setTimeout(() => {
      setIsProcessing(false);
      setCurrentPayload({
        assessment: "SAFE",
        certification: "VALID",
        synthesis: {
          summary: `Analysis complete for: "${query}". Conditions are optimal for marine operations in the designated sector.`,
          hazards: ["Minor swell (1.2m) approaching from South-East.", "Low visibility anticipated post 18:00 UTC."],
          directives: ["Proceed with standard route planning.", "Activate GEE Sea Surface Temp overlay to monitor thermal fronts.", "Maintain 15km distance from restricted MPA buffer zones."]
        },
        evidenceMet: 4,
        evidenceRequired: 4,
        sources: ["🛰 GEE (SST & Chlorophyll)", "🌊 INCOIS (Currents)", "🌦 Open-Meteo"],
        ragFootnotes: ["FAO Marine Safety Code (Sec 2.1)", "Coast Guard Geofencing Protocol 4A"],
        followups: ["Plot nearest PFZ hotspots", "Overlay Wave Height models"],
        
        // Dynamic Map Data to bring the canvas to life
        mapData: {
          startPoint: [17.431, 84.703],
          destinationPoint: [18.12, 85.10],
          activeRoute: [[17.431, 84.703], [17.65, 84.85], [17.90, 84.95], [18.12, 85.10]],
          pfzPoints: [{ position: [17.75, 84.90], label: "High Confidence PFZ" }, { position: [17.85, 85.05], label: "Moderate PFZ" }],
          overlayLayers: [] // In production, this would contain "https://earthengine.googleapis.com/v1alpha/projects/..." URLs
        }
      });
    }, 2800);
  };

  return (
    <div className="relative h-screen w-full bg-[#07111F] overflow-hidden font-sans flex">
      
      {/* MAP BACKGROUND (ABSOLUTE INSET-0) */}
      <div className="absolute inset-0 z-0">
        <MarineMap 
          activeRoute={currentPayload?.mapData?.activeRoute}
          startPoint={currentPayload?.mapData?.startPoint}
          destinationPoint={currentPayload?.mapData?.destinationPoint}
          pfzPoints={currentPayload?.mapData?.pfzPoints}
          overlayLayers={currentPayload?.mapData?.overlayLayers}
        />
      </div>

      {/* LEFT NAVIGATION (FLOATING) */}
      <div className="relative z-20 h-full w-64 flex-shrink-0 bg-[#0D1B2A]/70 backdrop-blur-xl border-r border-white/10 shadow-[5px_0_20px_rgba(0,0,0,0.5)]">
        <LeftNavigation />
      </div>

      {/* CENTER HUD & COMMAND BAR (FLOATING) */}
      <div className="relative z-10 flex-1 flex flex-col pointer-events-none">
        
        {/* Orchestration & Briefing Overlay Area */}
        <div className="flex-1 flex flex-col justify-end p-8 pb-12 items-start">
          
          {isProcessing && (
            <div className="pointer-events-auto">
              <OrchestrationHUD events={hudEvents} />
            </div>
          )}

          {(!isProcessing && currentPayload) && (
            <div className="pointer-events-auto">
              <BriefingCard 
                assessment={currentPayload.assessment}
                certification={currentPayload.certification}
                synthesis={currentPayload.synthesis}
                ragFootnotes={currentPayload.ragFootnotes}
                followups={currentPayload.followups}
                onFollowupClick={(action) => handleQuerySubmit(action, 'en-IN')} // The Dynamic Loop!
              />
            </div>
          )}

        </div>

        {/* FLOATING COMMAND PILL */}
        <div className="pointer-events-auto w-full flex justify-center pb-8">
          <div className="w-full max-w-3xl">
            <CommandBar onQuerySubmit={handleQuerySubmit} />
          </div>
        </div>

      </div>

      {/* RIGHT EVIDENCE LEDGER (FLOATING) */}
      {currentPayload && (
        <div className="relative z-20 h-full w-80 flex-shrink-0 bg-[#0D1B2A]/70 backdrop-blur-xl border-l border-white/10 shadow-[-5px_0_20px_rgba(0,0,0,0.5)] p-5">
          <EvidenceLedger 
            evidenceMet={currentPayload.evidenceMet}
            evidenceRequired={currentPayload.evidenceRequired}
            assessment={currentPayload.assessment}
            certification={currentPayload.certification}
            sources={currentPayload.sources}
          />
        </div>
      )}

    </div>
  );
};

export default IntelligenceConsole;
