import React, { useEffect, useRef, useState } from 'react';
import LeftNavigation from '../components/sidebars/LeftNavigation';
import EvidenceLedger from '../components/sidebars/EvidenceLedger';
import CommandBar from '../components/chat/CommandBar';
import BriefingCard from '../components/chat/BriefingCard';
import ResearchTrendChart from '../components/chat/ResearchTrendChart';
import OrchestrationHUD from '../components/timeline/OrchestrationHUD';
import { MapConsole } from '../components/map/MapConsole';
import { runIntelligenceQuery } from '../services/api';

const DEFAULT_LOCATION = { lat: 17.431, lon: 84.703 };
const HISTORY_STORAGE_KEY = 'orca-intelligence-query-history-v1';
const MAX_HISTORY_ITEMS = 8;

const readHistory = () => {
  try {
    const stored = window.localStorage.getItem(HISTORY_STORAGE_KEY);
    const parsed = stored ? JSON.parse(stored) : [];
    return Array.isArray(parsed) ? parsed.slice(0, MAX_HISTORY_ITEMS) : [];
  } catch {
    return [];
  }
};

const asFeatureCollection = (points) => {
  if (points?.type === 'FeatureCollection') return points;
  return { type: 'FeatureCollection', features: (points || []).map((point) => point.type === 'Feature' ? point : ({
    type: 'Feature', geometry: { type: 'Point', coordinates: [point.lon, point.lat] }, properties: point.properties || point
  })) };
};

const asRouteData = (route) => {
  if (!route) return null;
  if (route.path) return route;
  const coordinates = route?.geometry?.coordinates || route?.coordinates;
  if (!Array.isArray(coordinates)) return null;
  return { path: coordinates.map(([lon, lat], index) => ({ lon, lat, node_id: `route-${index}`, severity_score: 0 })) };
};

const asConversationContext = (payload, entry, destination) => ({
  requestId: payload.request_id || entry.id,
  intent: payload.intent,
  query: entry.query,
  location: entry.location,
  destination: payload.mapData?.destinationPoint || destination || null,
  language: entry.language,
  assessment: payload.assessment,
  certification: payload.certification,
  sourceStatus: (payload.execution?.sourceStatus || []).map(({ source, state, fetchedAt, cacheAgeSeconds }) => ({ source, state, fetchedAt, cacheAgeSeconds }))
});

const IntelligenceConsole = () => {
  const [state, setState] = useState('idle');
  const [currentPayload, setCurrentPayload] = useState(null);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState(DEFAULT_LOCATION);
  const [destination, setDestination] = useState(null);
  const [language, setLanguage] = useState('en-IN');
  const [queryHistory, setQueryHistory] = useState(readHistory);
  const [conversationContext, setConversationContext] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    let pendingQuery = '';
    try {
      pendingQuery = window.sessionStorage.getItem('orca-intelligence-pending-query') || '';
      window.sessionStorage.removeItem('orca-intelligence-pending-query');
    } catch {}
    if (pendingQuery) handleQuerySubmit(pendingQuery);
    // The pending query is written only by LandingPage navigation.  Running
    // once avoids re-submitting when ordinary Console state changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateHistory = (entry) => {
    setQueryHistory((previous) => {
      const next = [entry, ...previous.filter((item) => item.id !== entry.id && item.query !== entry.query)].slice(0, MAX_HISTORY_ITEMS);
      try { window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next)); } catch {}
      return next;
    });
  };

  const handleQuerySubmit = async (query, requestedLanguage = language, requestedLocation = location, requestedDestination = destination) => {
    abortRef.current?.abort();
    const requestId = crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`;
    const controller = new AbortController();
    abortRef.current = controller;
    setState('executing');
    setError(null);
    const historyEntry = { id: requestId, query, language: requestedLanguage, location: requestedLocation, state: 'RUNNING', createdAt: new Date().toISOString() };
    // The API receives only prior local questions; the in-flight question is
    // passed separately above.  Keeping the trace fields in the content makes
    // a future context resolver aware of the location and freshness of a turn.
    const recentHistory = queryHistory.slice(0, 5).reverse().map((entry) => ({
      role: 'user',
      content: `[${entry.createdAt || 'unknown time'}; ${entry.state || 'UNKNOWN'}; ${entry.language || 'en-IN'}; ${entry.location?.lat ?? 'unknown'}, ${entry.location?.lon ?? 'unknown'}] ${entry.query}`
    }));
    updateHistory(historyEntry);
    try {
      const payload = await runIntelligenceQuery({ request_id: requestId, query, latitude: requestedLocation.lat, longitude: requestedLocation.lon, destination_lat: requestedDestination?.lat, destination_lon: requestedDestination?.lon, language: requestedLanguage, history: recentHistory, conversation_context: conversationContext }, controller.signal);
      if (controller.signal.aborted) return;
      setCurrentPayload(payload);
      setConversationContext(asConversationContext(payload, historyEntry, requestedDestination));
      const responseState = payload.state === 'cached' ? 'CACHED' : 'LIVE';
      setState(payload.state === 'cached' ? 'cached' : 'live');
      updateHistory({ ...historyEntry, id: payload.request_id || requestId, state: responseState });
    } catch (requestError) {
      if (requestError.name === 'AbortError') return;
      setState('error');
      setError(requestError.message || 'The intelligence service did not return a result.');
      updateHistory({ ...historyEntry, state: 'FAILED' });
    }
  };

  const toggleOverlay = (overlayId) => setCurrentPayload((previous) => previous ? ({
    ...previous,
    mapData: { ...previous.mapData, overlayLayers: (previous.mapData?.overlayLayers || []).map((layer) =>
      layer.id === overlayId && layer.status !== 'UNAVAILABLE' ? { ...layer, visible: !layer.visible } : layer) }
  }) : previous);

  const routeToVerifiedPfz = () => {
    const point = currentPayload?.mapData?.pfzPoints?.[0];
    const lat = Number(point?.lat);
    const lon = Number(point?.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      setError('No verified PFZ coordinate is available for route calculation.');
      return;
    }
    const pfzDestination = { lat, lon };
    setDestination(pfzDestination);
    handleQuerySubmit('Find the safest route to this verified PFZ.', language, location, pfzDestination);
  };

  const mapData = currentPayload?.mapData || {};
  const contextResolution = currentPayload?.execution?.contextResolution;
  const isProcessing = state === 'executing';
  const agentStatuses = Object.entries(currentPayload?.execution?.agents || {});
  const sourceStatuses = currentPayload?.execution?.sourceStatus || [];
  const mapLayers = [...(mapData.overlayLayers || []), ...(mapData.disabledLayers || [])];
  const layerClassName = (layer) => {
    if (layer.status === 'UNAVAILABLE') return 'text-[#8FA8B8]';
    if (layer.status === 'STALE') return 'cursor-pointer text-[#FFB547]';
    return 'cursor-pointer text-[#EAF4F8]';
  };
  const layerStatusText = (layer) => {
    if (layer.status === 'UNAVAILABLE') return ` — ${layer.unavailableReason || 'Unavailable'}`;
    if (layer.status === 'STALE') {
      const age = layer.ageHours != null ? ` (${Math.round(layer.ageHours)}h old)` : '';
      return ` — STALE${age}: ${layer.staleReason || 'Satellite image is not current.'}`;
    }
    return '';
  };

  return (
    <main className="navik-daylight relative flex h-screen w-full overflow-hidden bg-[#07111F] font-sans text-[#EAF4F8]" aria-label="NAVIK AI Marine Intelligence Console">
      <div className="absolute inset-0 z-0"><MapConsole activeMode="routing" showLegend={false} pointAnalyticsEnabled selectedLocation={location} onLocationSelect={setLocation} destinationLocation={mapData.destinationPoint || destination} onDestinationSelect={setDestination} routeData={asRouteData(mapData.activeRoute || mapData.routeData)} pfzGeojson={asFeatureCollection(mapData.pfzGeojson || mapData.pfzPoints)} geofenceGeojson={mapData.geofences || null} gridGeojson={mapData.bsiGrid || null} vectorGrid={{ windGeojson: mapData.windVectors || null, currentGeojson: mapData.currentVectors || null }} layersOverride={{ bsiRisk: Boolean(mapData.bsiGrid?.features?.length), windVectors: Boolean(mapData.windVectors?.features?.length), currentVectors: Boolean(mapData.currentVectors?.features?.length), route: true, restricted: true, eezBorder: true }} overlayLayers={mapData.overlayLayers || []} /></div>

      <aside className="relative z-20 hidden h-full w-60 shrink-0 border-r border-[#20384D]/70 bg-[#07111F]/72 backdrop-blur-sm lg:block"><LeftNavigation history={queryHistory} agentState={state} onQuerySelect={(entry) => { if (entry.location) setLocation(entry.location); if (entry.query) handleQuerySubmit(entry.query, entry.language || 'en-IN', entry.location || location); }} /></aside>

      <section className="relative z-10 flex min-w-0 flex-1 flex-col pointer-events-none">
        <div className="relative flex min-h-0 flex-1 flex-col p-4 pb-3 sm:p-6">
          <div className="pointer-events-none min-h-0 flex-1 max-w-2xl overflow-y-auto pr-1 [scrollbar-width:thin] [&>*]:pointer-events-auto">
            {!currentPayload && !isProcessing && !error && <div className="max-w-md rounded-xl border border-[#20384D]/70 bg-[#07111F]/78 p-5 shadow-xl backdrop-blur-sm"><p className="font-mono text-xs uppercase tracking-[0.2em] text-[#00D4FF]">NAVIK AI · Marine Intelligence Console</p><h1 className="mt-3 text-xl font-semibold">Ask a marine operations question</h1><p className="mt-2 text-sm leading-relaxed text-[#8FA8B8]">Choose a vessel position, ask a question, and inspect the returned evidence. Source freshness is shown after the query; IMD official-warning verification remains pending.</p><p className="mt-4 font-mono text-[10px] uppercase tracking-wider text-[#8FA8B8]">Position · {location.lat.toFixed(3)}, {location.lon.toFixed(3)}{destination && ` · Destination ${destination.lat.toFixed(3)}, ${destination.lon.toFixed(3)}`}</p></div>}
            {currentPayload && <div className={`w-full origin-top-left transition-all duration-300 ${isProcessing ? 'scale-[0.98] opacity-40 grayscale' : ''}`}>{contextResolution?.applied && <p role="status" className="mb-2 max-w-2xl rounded-lg border border-[#00D4FF]/35 bg-[#07111F]/85 px-3 py-2 text-xs text-[#8FA8B8] backdrop-blur-sm">Using previous {contextResolution.resolvedIntent || 'marine'} context · {contextResolution.reason || 'location and evidence retained'}{contextResolution.missingRequirement ? ` · ${contextResolution.missingRequirement} required` : ''}</p>}<BriefingCard assessment={currentPayload.assessment} certification={currentPayload.certification} synthesis={currentPayload.synthesis} safetyEvidence={mapData.safetyEvidence} explainability={mapData.explainability} sourceStatuses={sourceStatuses} ragFootnotes={currentPayload.ragFootnotes} followups={currentPayload.followups} canRouteToPfz={currentPayload.intent === 'pfz' && Boolean(mapData.pfzPoints?.[0])} onRouteToPfz={routeToVerifiedPfz} narrativeAi={currentPayload.execution?.narrativeAi} language={language} onLanguageChange={setLanguage} onFollowupClick={(action) => handleQuerySubmit(action, language)} />{currentPayload.translation?.state === 'UNAVAILABLE' && language !== 'en-IN' && <p role="status" className="mt-2 max-w-2xl rounded-lg border border-[#FFB547]/35 bg-[#07111F]/85 px-3 py-2 text-xs text-[#FFB547] backdrop-blur-sm">Translation is unavailable for {language}; English evidence is shown. {currentPayload.translation.reason}</p>}</div>}
            {currentPayload?.intent === 'research' && <ResearchTrendChart series={mapData.historicalSeries} analysis={mapData.historicalAnalysis} papers={mapData.literaturePapers} />}
            {error && <div role="alert" className="max-w-lg rounded-xl border border-[#FF5C5C]/50 bg-[#07111F]/80 p-4 text-sm backdrop-blur-md"><p className="font-semibold text-[#FF5C5C]">Intelligence request failed</p><p className="mt-1 text-[#8FA8B8]">{error}</p></div>}
          </div>
          {isProcessing && <div className="pointer-events-auto absolute bottom-3 left-4 z-50 sm:left-6"><OrchestrationHUD events={['Planner', 'Weather evidence', 'Ocean / PFZ evidence', 'Geospatial safety', 'Risk and evidence validation'].map((text, index) => ({ status: index === 0 ? 'pending' : 'queued', text }))} /></div>}
          {(mapLayers.length > 0 || agentStatuses.length > 0) && <details className="pointer-events-auto mt-3 max-w-2xl rounded-xl border border-[#20384D]/70 bg-[#07111F]/90 px-3 py-2 shadow-xl backdrop-blur-sm"><summary className="cursor-pointer text-[10px] font-bold uppercase tracking-widest text-[#8FA8B8]">Intelligence layers & agent trace</summary><div className="mt-3 grid gap-3 md:grid-cols-2">{mapLayers.length > 0 && <div><p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-[#8FA8B8]">Scientific layers</p>{mapLayers.map((layer) => <label key={layer.id} className={`flex items-center justify-between gap-3 py-1 text-xs ${layerClassName(layer)}`}><span>{layer.title}{layerStatusText(layer)}</span><input aria-label={`Toggle ${layer.title}`} type="checkbox" checked={Boolean(layer.visible)} disabled={layer.status === 'UNAVAILABLE'} onChange={() => toggleOverlay(layer.id)} /></label>)}</div>}{agentStatuses.length > 0 && <div><div className="flex items-center justify-between"><p className="text-[10px] font-bold uppercase tracking-widest text-[#8FA8B8]">Agent trace</p><span className="font-mono text-[10px] text-[#00D4FF]">{currentPayload.execution?.totalLatencyMs ? `${Math.round(currentPayload.execution.totalLatencyMs)} ms` : 'complete'}</span></div><div className="mt-2 flex flex-wrap gap-2">{agentStatuses.map(([name, agentState]) => <span key={name} className={`rounded px-2 py-1 font-mono text-[10px] ${agentState === 'success' ? 'bg-[#18C7A0]/10 text-[#18C7A0]' : 'bg-[#FFB547]/10 text-[#FFB547]'}`}>{name} · {agentState}</span>)}</div>{sourceStatuses.length > 0 && <p className="mt-2 text-[10px] text-[#8FA8B8]">{sourceStatuses.map((source) => `${source.source}: ${source.state}`).join(' · ')}</p>}</div>}</div></details>}
        </div>
        <div className="pointer-events-auto flex w-full justify-center px-3 pb-4 sm:px-8 sm:pb-8"><div className="w-full max-w-3xl"><CommandBar onQuerySubmit={handleQuerySubmit} language={language} onLanguageChange={setLanguage} /></div></div>
      </section>

      {currentPayload && <aside className={`relative z-20 hidden h-full w-72 shrink-0 flex-col border-l border-[#20384D]/70 bg-[#07111F]/72 p-4 backdrop-blur-sm xl:flex ${isProcessing ? 'pointer-events-none opacity-40' : ''}`}><div className="mb-3 shrink-0 text-[10px] font-mono uppercase tracking-widest text-[#8FA8B8]">{state === 'cached' ? 'Cached evidence' : 'Live evidence'} · {currentPayload.request_id?.slice(0, 8) || 'untraced'}</div><EvidenceLedger className="min-h-0 flex-1" evidenceMet={currentPayload.evidenceMet} evidenceRequired={currentPayload.evidenceRequired} assessment={currentPayload.assessment} certification={currentPayload.certification} sources={currentPayload.sources} ragFootnotes={currentPayload.ragFootnotes} isSafetyFloorTriggered={currentPayload.isSafetyFloorTriggered} /></aside>}
    </main>
  );
};

export default IntelligenceConsole;
