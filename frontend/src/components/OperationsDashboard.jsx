import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import WorkspaceNav from './navigation/WorkspaceNav';
import TopHeader from './navigation/TopHeader';
import MapConsole from './map/MapConsole';
import RoutingSidebar from './sidebars/RoutingSidebar';
import FisheriesSidebar from './sidebars/FisheriesSidebar';
import WeatherSidebar from './sidebars/WeatherSidebar';
import WeatherTimelinePanel from './timeline/WeatherTimelinePanel';
import SafetyAdvisorChat from './chat/SafetyAdvisorChat';
import SpotlightCard from './common/SpotlightCard';
import { getSafety, getForecast, getGrid, getAdvisories, getGeofence, getPfzLines, getVectorGrid, calculateRoute } from '../services/api';

const VALID_MODES = ['routing', 'fisheries', 'weather'];
const HOURS = [0, 3, 6, 9, 12, 15, 18, 21];
const INITIAL_LOCATION = { lat: 18.9220, lon: 72.8347 };
const INITIAL_DESTINATION = { lat: 10.5667, lon: 72.6417 };
const EMPTY_FEATURE_COLLECTION = { type: 'FeatureCollection', features: [] };
const EMPTY_VECTOR_GRID = { windGeojson: EMPTY_FEATURE_COLLECTION, currentGeojson: EMPTY_FEATURE_COLLECTION, timestamp: null };
const INITIAL_STATUS = { safety: 'loading', forecast: 'loading', grid: 'loading', vectors: 'loading', advisories: 'loading', geofence: 'loading', pfz: 'loading' };

const resultOf = promise => promise.then(data => ({ ok: true, data })).catch(error => ({ ok: false, error }));

function classifyPayload(payload) {
  const source = String(payload?.source || payload?.provenance?.source || payload?.metadata?.source || '').toLowerCase();
  if (source.includes('fallback') || source.includes('open-meteo') || source.includes('mock')) return 'fallback';
  if (source.includes('cache')) return 'cached';
  return 'live';
}

export function OperationsDashboard({ onBackToLanding, initialMode = 'routing' }) {
  const { mode: urlMode } = useParams();
  const navigate = useNavigate();
  const resolvedMode = urlMode === 'advisor' ? 'routing' : (VALID_MODES.includes(urlMode) ? urlMode : (initialMode === 'advisor' ? 'routing' : initialMode || 'routing'));

  const [activeMode, setActiveMode] = useState(resolvedMode);
  const [isChatOpen, setIsChatOpen] = useState(urlMode === 'advisor' || initialMode === 'advisor');
  const [selectedLocation, setSelectedLocation] = useState(INITIAL_LOCATION);
  const [destinationLocation, setDestinationLocation] = useState(INITIAL_DESTINATION);
  const [beamWidth, setBeamWidth] = useState(3.5);
  const [selectedDay, setSelectedDay] = useState(1);
  const [selectedHour, setSelectedHour] = useState(12);

  const [safetyData, setSafetyData] = useState(null);
  const [forecastTimeline, setForecastTimeline] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [gridGeojson, setGridGeojson] = useState(EMPTY_FEATURE_COLLECTION);
  const [advisoriesGeojson, setAdvisoriesGeojson] = useState(EMPTY_FEATURE_COLLECTION);
  const [geofenceGeojson, setGeofenceGeojson] = useState(EMPTY_FEATURE_COLLECTION);
  const [pfzGeojson, setPfzGeojson] = useState(EMPTY_FEATURE_COLLECTION);
  const [vectorGrid, setVectorGrid] = useState(EMPTY_VECTOR_GRID);
  const [dataStatus, setDataStatus] = useState(INITIAL_STATUS);
  const [sstOpacity, setSstOpacity] = useState(0.65);
  const [chlOpacity, setChlOpacity] = useState(0.65);
  const [selectedPfz, setSelectedPfz] = useState(null);
  const [layersOverride, setLayersOverride] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRouteLoading, setIsRouteLoading] = useState(false);

  useEffect(() => {
    if (urlMode === 'advisor') { setActiveMode('routing'); setIsChatOpen(true); }
    else if (urlMode && VALID_MODES.includes(urlMode)) setActiveMode(urlMode);
    else if (urlMode && !VALID_MODES.includes(urlMode)) navigate('/console/routing', { replace: true });
  }, [urlMode, navigate]);

  const handleModeChange = useCallback(mode => {
    if (VALID_MODES.includes(mode)) { setActiveMode(mode); navigate(`/console/${mode}`); }
  }, [navigate]);

  const handleReturnToLanding = useCallback(() => onBackToLanding ? onBackToLanding() : navigate('/'), [onBackToLanding, navigate]);

  // Exact selected location/day/hour -> authoritative safety assessment.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, safety: 'loading' }));
    resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour)).then(result => {
      if (!active) return;
      if (result.ok) { setSafetyData(result.data); setDataStatus(prev => ({ ...prev, safety: classifyPayload(result.data) })); }
      else setDataStatus(prev => ({ ...prev, safety: 'unavailable' }));
    });
    return () => { active = false; };
  }, [selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour]);

  // Exact selected location/day -> 24-hour forecast.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, forecast: 'loading' }));
    resultOf(getForecast(selectedLocation.lat, selectedLocation.lon, selectedDay)).then(result => {
      if (!active) return;
      if (result.ok) { setForecastTimeline(result.data); setDataStatus(prev => ({ ...prev, forecast: classifyPayload(result.data) })); }
      else setDataStatus(prev => ({ ...prev, forecast: 'unavailable' }));
    });
    return () => { active = false; };
  }, [selectedLocation.lat, selectedLocation.lon, selectedDay]);

  // Exact selected day/hour -> BSI grid + vector field.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, grid: 'loading', vectors: 'loading' }));
    Promise.all([resultOf(getGrid(selectedDay, selectedHour)), resultOf(getVectorGrid(selectedDay, selectedHour))]).then(([grid, vectors]) => {
      if (!active) return;
      if (grid.ok) { setGridGeojson(grid.data); setDataStatus(prev => ({ ...prev, grid: classifyPayload(grid.data) })); }
      else setDataStatus(prev => ({ ...prev, grid: 'unavailable' }));
      if (vectors.ok) { setVectorGrid(vectors.data); setDataStatus(prev => ({ ...prev, vectors: classifyPayload(vectors.data) })); }
      else { setVectorGrid(EMPTY_VECTOR_GRID); setDataStatus(prev => ({ ...prev, vectors: 'unavailable' })); }
    });
    return () => { active = false; };
  }, [selectedDay, selectedHour]);

  // Location-independent operational overlays.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, advisories: 'loading', geofence: 'loading', pfz: 'loading' }));
    Promise.all([resultOf(getAdvisories()), resultOf(getGeofence()), resultOf(getPfzLines())]).then(([advisories, geofence, pfz]) => {
      if (!active) return;
      if (advisories.ok) { setAdvisoriesGeojson(advisories.data); setDataStatus(prev => ({ ...prev, advisories: classifyPayload(advisories.data) })); }
      else setDataStatus(prev => ({ ...prev, advisories: 'unavailable' }));
      if (geofence.ok) { setGeofenceGeojson(geofence.data); setDataStatus(prev => ({ ...prev, geofence: classifyPayload(geofence.data) })); }
      else setDataStatus(prev => ({ ...prev, geofence: 'unavailable' }));
      if (pfz.ok) { setPfzGeojson(pfz.data); setDataStatus(prev => ({ ...prev, pfz: classifyPayload(pfz.data) })); }
      else setDataStatus(prev => ({ ...prev, pfz: 'unavailable' }));
    });
    return () => { active = false; };
  }, []);

  const handleCalculateRoute = useCallback(async () => {
    setIsRouteLoading(true);
    try { setRouteData(await calculateRoute(selectedLocation, destinationLocation, beamWidth, selectedDay, selectedHour)); }
    catch (error) { console.warn('[OperationsDashboard] Route unavailable:', error); setRouteData(null); }
    finally { setIsRouteLoading(false); }
  }, [selectedLocation, destinationLocation, beamWidth, selectedDay, selectedHour]);

  const handleClearRoute = useCallback(() => setRouteData(null), []);

  // Seven dynamic datasets: all requests start together and each result is tracked independently.
  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    setDataStatus({ safety: 'loading', forecast: 'loading', grid: 'loading', vectors: 'loading', advisories: 'loading', geofence: 'loading', pfz: 'loading' });

    const [safety, forecast, grid, vectors, advisories, geofence, pfz] = await Promise.all([
      resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour)),
      resultOf(getForecast(selectedLocation.lat, selectedLocation.lon, selectedDay)),
      resultOf(getGrid(selectedDay, selectedHour)),
      resultOf(getVectorGrid(selectedDay, selectedHour)),
      resultOf(getAdvisories()),
      resultOf(getGeofence()),
      resultOf(getPfzLines())
    ]);

    if (safety.ok) setSafetyData(safety.data);
    if (forecast.ok) setForecastTimeline(forecast.data);
    if (grid.ok) setGridGeojson(grid.data);
    if (vectors.ok) setVectorGrid(vectors.data); else setVectorGrid(EMPTY_VECTOR_GRID);
    if (advisories.ok) setAdvisoriesGeojson(advisories.data);
    if (geofence.ok) setGeofenceGeojson(geofence.data);
    if (pfz.ok) setPfzGeojson(pfz.data);

    setDataStatus({
      safety: safety.ok ? classifyPayload(safety.data) : 'unavailable',
      forecast: forecast.ok ? classifyPayload(forecast.data) : 'unavailable',
      grid: grid.ok ? classifyPayload(grid.data) : 'unavailable',
      vectors: vectors.ok ? classifyPayload(vectors.data) : 'unavailable',
      advisories: advisories.ok ? classifyPayload(advisories.data) : 'unavailable',
      geofence: geofence.ok ? classifyPayload(geofence.data) : 'unavailable',
      pfz: pfz.ok ? classifyPayload(pfz.data) : 'unavailable'
    });
    setIsLoading(false);
  }, [selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour]);

  const overallRisk = routeData?.summary?.overall_risk || safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';
  const liveContext = {
    active_workspace: activeMode === 'routing' ? 'Tactical Routing' : activeMode === 'fisheries' ? 'Ocean Analytics' : 'Meteorological Hazards',
    origin_coords: selectedLocation,
    destination_coords: destinationLocation,
    beam_width: `${beamWidth.toFixed(1)}m`,
    current_risk_score: overallRisk,
    bsi_score: safetyData?.bsi_metrics?.bsi_score ?? null,
    max_wave_height: safetyData?.raw_metrics?.inspect_hs != null ? `${Number(safetyData.raw_metrics.inspect_hs).toFixed(1)}m` : 'N/A',
    wind_speed: safetyData?.raw_metrics?.wind_speed_kmh != null ? `${Number(safetyData.raw_metrics.wind_speed_kmh).toFixed(1)} km/h` : 'N/A',
    distance_to_border: safetyData?.raw_metrics?.distance_to_border_km != null ? `${Number(safetyData.raw_metrics.distance_to_border_km).toFixed(1)} km` : 'N/A',
    avoided_hazards: routeData?.summary?.avoided_hazards || []
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07111F] text-[#EAF4F8] font-sans overflow-hidden select-none">
      <TopHeader activeMode={activeMode} selectedLocation={selectedLocation} safetyData={safetyData} dataStatus={dataStatus} isLoading={isLoading} onRefresh={handleRefresh} onBackToLanding={handleReturnToLanding} onToggleChat={() => setIsChatOpen(!isChatOpen)} isChatOpen={isChatOpen} />
      <div className="flex flex-1 overflow-hidden relative">
        <WorkspaceNav activeMode={activeMode} setActiveMode={handleModeChange} onToggleChat={() => setIsChatOpen(!isChatOpen)} isChatOpen={isChatOpen} onBackToLanding={handleReturnToLanding} />
        <div className="w-[360px] sm:w-[380px] lg:w-[420px] min-w-[320px] h-full bg-[#0D1B2A] border-r border-[#20384D] flex flex-col shrink-0 z-10">
          <SpotlightCard className="h-full rounded-none border-0 bg-transparent flex flex-col">
            {activeMode === 'routing' && <RoutingSidebar selectedLocation={selectedLocation} onLocationSelect={setSelectedLocation} destinationLocation={destinationLocation} onDestinationSelect={setDestinationLocation} beamWidth={beamWidth} setBeamWidth={setBeamWidth} onCalculateRoute={handleCalculateRoute} onClearRoute={handleClearRoute} routeData={routeData} safetyData={safetyData} isLoading={isRouteLoading} />}
            {activeMode === 'fisheries' && <FisheriesSidebar sstOpacity={sstOpacity} setSstOpacity={setSstOpacity} chlOpacity={chlOpacity} setChlOpacity={setChlOpacity} pfzList={pfzGeojson.features || []} selectedPfz={selectedPfz} onSelectPfz={setSelectedPfz} onDestinationSelect={setDestinationLocation} selectedLocation={selectedLocation} layersOverride={layersOverride} setLayersOverride={setLayersOverride} />}
            {activeMode === 'weather' && <WeatherSidebar selectedDay={selectedDay} setSelectedDay={setSelectedDay} selectedHour={selectedHour} setSelectedHour={hour => HOURS.includes(hour) && setSelectedHour(hour)} safetyData={safetyData} layersOverride={layersOverride} setLayersOverride={setLayersOverride} />}
          </SpotlightCard>
        </div>
        <main className="flex-1 flex flex-col h-full bg-[#07111F] relative overflow-hidden">
          <div className="flex-1 relative">
            <MapConsole activeMode={activeMode} selectedLocation={selectedLocation} onLocationSelect={setSelectedLocation} destinationLocation={destinationLocation} onDestinationSelect={setDestinationLocation} routeData={routeData} pfzGeojson={pfzGeojson} vectorGrid={vectorGrid} advisoriesGeojson={advisoriesGeojson} geofenceGeojson={geofenceGeojson} gridGeojson={gridGeojson} sstOpacity={sstOpacity} chlOpacity={chlOpacity} beamWidth={beamWidth} layersOverride={layersOverride} onPfzInspect={pfzFeature => { setSelectedPfz(pfzFeature); if (activeMode !== 'fisheries') handleModeChange('fisheries'); }} />
          </div>
          <WeatherTimelinePanel forecastTimeline={forecastTimeline} selectedHour={selectedHour} onSelectHour={hour => HOURS.includes(hour) && setSelectedHour(hour)} selectedDay={selectedDay} />
        </main>
        <SafetyAdvisorChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} liveContext={liveContext} activeMode={activeMode} />
      </div>
    </div>
  );
}

export default OperationsDashboard;
