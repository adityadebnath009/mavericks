import React, { useState, useEffect, useCallback, useRef } from 'react';
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
import { getSafety, getForecast, getGrid, getAdvisories, getGeofence, getGeofenceStatus, getPfzLines, getVectorGrid, calculateRoute } from '../services/api';

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

const distanceBetweenPositions = (a, b) => {
  if (!a || !b) return Number.POSITIVE_INFINITY;
  const latScale = 111;
  const lonScale = Math.cos(((Number(a.lat) + Number(b.lat)) / 2) * Math.PI / 180) * 111;
  return Math.hypot((Number(a.lat) - Number(b.lat)) * latScale, (Number(a.lon) - Number(b.lon)) * lonScale);
};

const boundaryAlertFromStatus = (status, extra = {}) => {
  if (!status || typeof status.status !== 'string') {
    return { level: 'UNAVAILABLE', rank: -1, title: 'Boundary status unavailable', message: 'Known EEZ and MPA boundaries could not be evaluated for this simulated position.', ...extra };
  }
  const borderDistance = Number(status.distance_to_border_km);
  const mpaDistance = Number(status.distance_to_mpa_km);
  const nearestIsMpa = Number.isFinite(mpaDistance) && mpaDistance < borderDistance;
  const boundaryName = status.mpa_name || (nearestIsMpa ? 'known marine protected area' : 'Indian EEZ boundary');
  const distanceKm = nearestIsMpa ? mpaDistance : borderDistance;
  const isDanger = status.status === 'DANGER_INSIDE_RESTRICTED_ZONE' || status.status === 'DANGER_OUTSIDE_BORDER';
  const isWarning = status.status === 'WARNING_APPROACHING_BORDER' || status.status === 'WARNING_APPROACHING_RESTRICTED_ZONE';
  const isWatch = !isDanger && !isWarning && ((nearestIsMpa && mpaDistance <= 4) || (!nearestIsMpa && borderDistance <= 10));
  const level = isDanger ? 'DANGER' : isWarning ? 'WARNING' : isWatch ? 'WATCH' : 'SAFE';
  const rank = { SAFE: 0, WATCH: 1, WARNING: 2, DANGER: 3 }[level];
  const instruction = level === 'DANGER'
    ? (status.status === 'DANGER_INSIDE_RESTRICTED_ZONE' ? 'Leave the protected area immediately; fishing is not permitted here.' : 'Turn back toward the marked safe corridor immediately.')
    : level === 'WARNING'
      ? `Keep clear of the ${boundaryName}; do not continue toward the boundary.`
      : level === 'WATCH'
        ? `Monitor your course and maintain a safe margin from the ${boundaryName}.`
        : 'No nearby known EEZ or MPA restriction is detected at this simulated position.';
  return { level, rank, boundaryName, distanceKm, message: status.message, instruction, status, ...extra };
};

export function OperationsDashboard({ onBackToLanding, initialMode = 'routing' }) {
  const { mode: urlMode } = useParams();
  const navigate = useNavigate();
  const resolvedMode = urlMode === 'advisor' ? 'routing' : (VALID_MODES.includes(urlMode) ? urlMode : (initialMode === 'advisor' ? 'routing' : initialMode || 'routing'));

  const [activeMode, setActiveMode] = useState(resolvedMode);
  const [isChatOpen, setIsChatOpen] = useState(urlMode === 'advisor' || initialMode === 'advisor');
  const [routeError, setRouteError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(INITIAL_LOCATION);
  const [destinationLocation, setDestinationLocation] = useState(INITIAL_DESTINATION);
  const [vesselProfile, setVesselProfile] = useState({ length_m: 10.0, beam_m: 3.5, cruising_speed_kn: 10.0 });
  const [currentTime, setCurrentTime] = useState(new Date().toISOString());
  const [departureTime, setDepartureTime] = useState(new Date().toISOString());
  const [isDepartureManual, setIsDepartureManual] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date().toISOString();
      setCurrentTime(now);
      if (!isDepartureManual) {
        setDepartureTime(now);
      }
    }, 1000); // Tick every second to keep the clock precisely aligned
    return () => clearInterval(timer);
  }, [isDepartureManual]);
  const [selectedDay, setSelectedDay] = useState(1);
  const [selectedHour, setSelectedHour] = useState(12);
  const [selectedNodeId, setSelectedNodeId] = useState(null);

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
  const [hoveredPfzId, setHoveredPfzId] = useState(null);
  const [layersOverride, setLayersOverride] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRouteLoading, setIsRouteLoading] = useState(false);
  const [simulationEnabled, setSimulationEnabled] = useState(false);
  const [simulationPosition, setSimulationPosition] = useState(null);
  const [simulationPlaying, setSimulationPlaying] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(1);
  const [simulationProgress, setSimulationProgress] = useState(0);
  const [simulationNodeIndex, setSimulationNodeIndex] = useState(0);
  const [boundaryAlert, setBoundaryAlert] = useState(null);
  const [routeAheadAlert, setRouteAheadAlert] = useState(null);
  const [notificationPermission, setNotificationPermission] = useState(() => (
    typeof Notification === 'undefined' ? 'unsupported' : Notification.permission
  ));
  const boundaryRequestRef = useRef(0);
  const previousBoundaryAlertRef = useRef(null);
  const playbackProgressRef = useRef(0);

  // Geolocation: Auto-detect user's actual location on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setSelectedLocation({ lat: position.coords.latitude, lon: position.coords.longitude });
        },
        (error) => {
          console.warn("Geolocation denied or failed. Defaulting to Mumbai.", error);
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    }
  }, []);

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
    resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, vesselProfile.beam_m, selectedDay, selectedHour)).then(result => {
      if (!active) return;
      if (result.ok) { setSafetyData(result.data); setDataStatus(prev => ({ ...prev, safety: classifyPayload(result.data) })); }
      else setDataStatus(prev => ({ ...prev, safety: 'unavailable' }));
    });
    return () => { active = false; };
  }, [selectedLocation.lat, selectedLocation.lon, vesselProfile.beam_m, selectedDay, selectedHour]);

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

  const evaluateSimulationPosition = useCallback(async (position, { notify = true, routeNode = null } = {}) => {
    const requestId = ++boundaryRequestRef.current;
    try {
      const status = await getGeofenceStatus(position.lat, position.lon);
      if (requestId !== boundaryRequestRef.current) return null;
      const alert = boundaryAlertFromStatus(status, { position, evaluatedAt: new Date().toISOString(), routeNode });
      const previous = previousBoundaryAlertRef.current;
      const boundaryChanged = previous && previous.boundaryName !== alert.boundaryName;
      const shouldNotify = notify && notificationPermission === 'granted' && typeof Notification !== 'undefined'
        && (alert.rank > (previous?.rank ?? -1) || (boundaryChanged && alert.rank >= 2));
      if (shouldNotify) {
        new Notification(`NAVIK boundary ${alert.level.toLowerCase()}`, { body: `${alert.boundaryName}: ${alert.instruction}` });
      }
      previousBoundaryAlertRef.current = alert;
      setBoundaryAlert(alert);
      return alert;
    } catch (error) {
      if (requestId !== boundaryRequestRef.current) return null;
      const unavailable = boundaryAlertFromStatus(null, { position, evaluatedAt: new Date().toISOString(), reason: error.message, routeNode });
      previousBoundaryAlertRef.current = unavailable;
      setBoundaryAlert(unavailable);
      return unavailable;
    }
  }, [notificationPermission]);

  const scanRouteBoundaries = useCallback(async (path) => {
    if (!Array.isArray(path) || path.length === 0) {
      setRouteAheadAlert(null);
      return;
    }
    const results = await Promise.allSettled(path.map(async node => ({ node, status: await getGeofenceStatus(node.lat, node.lon) })));
    const evaluated = results
      .filter(result => result.status === 'fulfilled')
      .map(result => boundaryAlertFromStatus(result.value.status, { position: result.value.node, routeNode: result.value.node }));
    if (evaluated.length === 0) {
      setRouteAheadAlert(boundaryAlertFromStatus(null, { reason: 'Route boundary scan failed.' }));
      return;
    }
    setRouteAheadAlert(evaluated.find(alert => alert.rank > 0) || null);
  }, []);

  const nearestRouteNodeIndex = useCallback((position, path = routeData?.path) => {
    if (!Array.isArray(path) || path.length === 0) return 0;
    return path.reduce((best, node, index) => (
      distanceBetweenPositions(position, node) < distanceBetweenPositions(position, path[best]) ? index : best
    ), 0);
  }, [routeData]);

  const handleSimulationPositionChange = useCallback((position) => {
    setSimulationPlaying(false);
    const nodeIndex = nearestRouteNodeIndex(position);
    playbackProgressRef.current = nodeIndex;
    setSimulationProgress(nodeIndex);
    setSimulationNodeIndex(nodeIndex);
    setSelectedNodeId(routeData?.path?.[nodeIndex]?.node_id || null);
    setSimulationPosition(position);
    evaluateSimulationPosition(position, { routeNode: routeData?.path?.[nodeIndex] || null });
  }, [evaluateSimulationPosition, nearestRouteNodeIndex, routeData]);

  const handleSimulationEnabledChange = useCallback((enabled) => {
    setSimulationEnabled(enabled);
    setSimulationPlaying(false);
    if (!enabled) return;
    const start = routeData?.path?.[0] || selectedLocation;
    playbackProgressRef.current = 0;
    setSimulationProgress(0);
    setSimulationNodeIndex(0);
    setSelectedNodeId(routeData?.path?.[0]?.node_id || null);
    setSimulationPosition({ lat: start.lat, lon: start.lon });
    evaluateSimulationPosition(start, { routeNode: routeData?.path?.[0] || null });
  }, [evaluateSimulationPosition, routeData, selectedLocation]);

  const handleSimulationReset = useCallback(() => {
    const start = routeData?.path?.[0] || selectedLocation;
    setSimulationPlaying(false);
    playbackProgressRef.current = 0;
    setSimulationProgress(0);
    setSimulationNodeIndex(0);
    setSelectedNodeId(routeData?.path?.[0]?.node_id || null);
    setSimulationPosition({ lat: start.lat, lon: start.lon });
    evaluateSimulationPosition(start, { routeNode: routeData?.path?.[0] || null });
  }, [evaluateSimulationPosition, routeData, selectedLocation]);

  const requestBrowserNotifications = useCallback(async () => {
    if (typeof Notification === 'undefined') {
      setNotificationPermission('unsupported');
      return;
    }
    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);
  }, []);

  useEffect(() => {
    if (!simulationEnabled || !simulationPlaying || !routeData?.path || routeData.path.length < 2) return undefined;
    const path = routeData.path;
    let lastNodeIndex = Math.floor(playbackProgressRef.current);
    const segmentDurationMs = 4000 / simulationSpeed;
    const timer = setInterval(() => {
      const nextProgress = Math.min(path.length - 1, playbackProgressRef.current + 100 / segmentDurationMs);
      playbackProgressRef.current = nextProgress;
      const startIndex = Math.floor(nextProgress);
      const endIndex = Math.min(startIndex + 1, path.length - 1);
      const fraction = nextProgress - startIndex;
      const position = {
        lat: path[startIndex].lat + (path[endIndex].lat - path[startIndex].lat) * fraction,
        lon: path[startIndex].lon + (path[endIndex].lon - path[startIndex].lon) * fraction,
      };
      setSimulationProgress(nextProgress);
      setSimulationPosition(position);
      if (startIndex !== lastNodeIndex || nextProgress === path.length - 1) {
        lastNodeIndex = startIndex;
        setSimulationNodeIndex(startIndex);
        setSelectedNodeId(path[startIndex].node_id || null);
        evaluateSimulationPosition(position, { routeNode: path[startIndex] });
      }
      if (nextProgress >= path.length - 1) setSimulationPlaying(false);
    }, 100);
    return () => clearInterval(timer);
  }, [evaluateSimulationPosition, routeData, simulationEnabled, simulationPlaying, simulationSpeed]);

  useEffect(() => {
    if (activeMode !== 'routing') setSimulationPlaying(false);
  }, [activeMode]);

  const handleCalculateRoute = useCallback(async () => {
    setIsRouteLoading(true);
    setRouteError(null);
    try { 
      const calculatedRoute = await calculateRoute(selectedLocation, destinationLocation, vesselProfile, departureTime);
      setRouteData(calculatedRoute);
      setSimulationPlaying(false);
      setSimulationProgress(0);
      playbackProgressRef.current = 0;
      setSimulationNodeIndex(0);
      if (simulationEnabled && calculatedRoute.path?.[0]) {
        const start = calculatedRoute.path[0];
        setSimulationPosition({ lat: start.lat, lon: start.lon });
        evaluateSimulationPosition(start, { routeNode: start });
      }
      scanRouteBoundaries(calculatedRoute.path);
    }
    catch (error) { 
      console.warn('[OperationsDashboard] Route unavailable:', error); 
      setRouteData(null); 
      setRouteError(error.message || "Route calculation failed.");
    }
    finally { setIsRouteLoading(false); }
  }, [selectedLocation, destinationLocation, vesselProfile, departureTime, selectedDay, selectedHour, evaluateSimulationPosition, scanRouteBoundaries, simulationEnabled]);

  const handleClearRoute = useCallback(() => {
    setRouteData(null);
    setRouteError(null);
    setSimulationPlaying(false);
    setRouteAheadAlert(null);
    setSelectedNodeId(null);
  }, []);

  // Seven dynamic datasets: all requests start together and each result is tracked independently.
  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    setDataStatus({ safety: 'loading', forecast: 'loading', grid: 'loading', vectors: 'loading', advisories: 'loading', geofence: 'loading', pfz: 'loading' });

    const [safety, forecast, grid, vectors, advisories, geofence, pfz] = await Promise.all([
      resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, vesselProfile.beam_m, selectedDay, selectedHour)),
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
  }, [selectedLocation.lat, selectedLocation.lon, vesselProfile.beam_m, selectedDay, selectedHour]);

  const overallRisk = routeData?.summary?.overall_risk || safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';
  const liveContext = {
    active_workspace: activeMode === 'routing' ? 'Tactical Routing' : activeMode === 'fisheries' ? 'Ocean Analytics' : 'Meteorological Hazards',
    origin_coords: selectedLocation,
    destination_coords: destinationLocation,
    beam_width: `${(vesselProfile?.beam_m || 3.5).toFixed(1)}m`,
    current_risk_score: overallRisk,
    bsi_score: safetyData?.bsi_metrics?.bsi_score ?? null,
    max_wave_height: safetyData?.raw_metrics?.inspect_hs != null ? `${Number(safetyData.raw_metrics.inspect_hs).toFixed(1)}m` : 'N/A',
    wind_speed: safetyData?.raw_metrics?.wind_speed_kmh != null ? `${Number(safetyData.raw_metrics.wind_speed_kmh).toFixed(1)} km/h` : 'N/A',
    distance_to_border: safetyData?.raw_metrics?.distance_to_border_km != null ? `${Number(safetyData.raw_metrics.distance_to_border_km).toFixed(1)} km` : 'N/A',
    avoided_hazards: routeData?.summary?.avoided_hazards || []
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07111F] text-[#EAF4F8] font-sans overflow-hidden select-none">
      <TopHeader activeMode={activeMode} selectedLocation={selectedLocation} safetyData={safetyData} dataStatus={dataStatus} isLoading={isLoading} onRefresh={handleRefresh} onBackToLanding={handleReturnToLanding} onToggleChat={() => setIsChatOpen(!isChatOpen)} isChatOpen={isChatOpen} currentTime={currentTime} />
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Layer 0: Edge-to-Edge Map Canvas */}
        <div className="absolute inset-0 z-0">
          <MapConsole activeMode={activeMode} selectedLocation={selectedLocation} onLocationSelect={setSelectedLocation} simulationEnabled={simulationEnabled && activeMode === 'routing'} simulationVesselPosition={simulationPosition} onSimulationPositionChange={handleSimulationPositionChange} destinationLocation={destinationLocation} onDestinationSelect={setDestinationLocation} routeData={routeData} pfzGeojson={pfzGeojson} vectorGrid={vectorGrid} advisoriesGeojson={advisoriesGeojson} geofenceGeojson={geofenceGeojson} gridGeojson={gridGeojson} sstOpacity={sstOpacity} chlOpacity={chlOpacity} beamWidth={vesselProfile.beam_m} layersOverride={layersOverride} onPfzInspect={pfzFeature => { setSelectedPfz(pfzFeature); if (activeMode !== 'fisheries') handleModeChange('fisheries'); }} selectedNodeId={selectedNodeId} onNodeSelect={setSelectedNodeId} selectedPfz={selectedPfz} hoveredPfzId={hoveredPfzId} onHoverPfz={setHoveredPfzId} />
        </div>

        {/* Layer 1: Floating UI with Glassmorphism */}
        <div className="relative z-10 flex h-full w-full pointer-events-none">
          
          {/* Navigation */}
          <div className="pointer-events-auto shrink-0 flex h-full">
            <WorkspaceNav activeMode={activeMode} setActiveMode={handleModeChange} onToggleChat={() => setIsChatOpen(!isChatOpen)} isChatOpen={isChatOpen} onBackToLanding={handleReturnToLanding} />
          </div>
          
          {/* V2 Glassmorphism Sidebar */}
          <div className="pointer-events-auto w-[360px] sm:w-[380px] lg:w-[420px] min-w-[320px] h-full bg-[#0D1B2A]/75 backdrop-blur-md border-r border-[#20384D]/50 shadow-2xl flex flex-col shrink-0 transition-all duration-300">
            <SpotlightCard className="h-full rounded-none border-0 bg-transparent flex flex-col">
              {activeMode === 'routing' && <RoutingSidebar selectedLocation={selectedLocation} onLocationSelect={setSelectedLocation} destinationLocation={destinationLocation} onDestinationSelect={setDestinationLocation} vesselProfile={vesselProfile} setVesselProfile={setVesselProfile} departureTime={departureTime} setDepartureTime={setDepartureTime} isDepartureManual={isDepartureManual} setIsDepartureManual={setIsDepartureManual} onCalculateRoute={handleCalculateRoute} onClearRoute={handleClearRoute} routeData={routeData} safetyData={safetyData} isLoading={isRouteLoading} error={routeError} simulationEnabled={simulationEnabled} onSimulationEnabledChange={handleSimulationEnabledChange} simulationPlaying={simulationPlaying} onSimulationPlayingChange={setSimulationPlaying} simulationSpeed={simulationSpeed} onSimulationSpeedChange={setSimulationSpeed} onSimulationReset={handleSimulationReset} boundaryAlert={boundaryAlert} routeAheadAlert={routeAheadAlert} simulationNodeIndex={simulationNodeIndex} simulationProgress={simulationProgress} notificationPermission={notificationPermission} onRequestBrowserNotifications={requestBrowserNotifications} />}
              {activeMode === 'fisheries' && <FisheriesSidebar sstOpacity={sstOpacity} setSstOpacity={setSstOpacity} chlOpacity={chlOpacity} setChlOpacity={setChlOpacity} pfzList={pfzGeojson.features || []} selectedPfz={selectedPfz} onSelectPfz={setSelectedPfz} onDestinationSelect={setDestinationLocation} selectedLocation={selectedLocation} layersOverride={layersOverride} setLayersOverride={setLayersOverride} hoveredPfzId={hoveredPfzId} onHoverPfz={setHoveredPfzId} />}
              {activeMode === 'weather' && <WeatherSidebar selectedDay={selectedDay} setSelectedDay={setSelectedDay} selectedHour={selectedHour} setSelectedHour={hour => HOURS.includes(hour) && setSelectedHour(hour)} safetyData={safetyData} layersOverride={layersOverride} setLayersOverride={setLayersOverride} />}
            </SpotlightCard>
          </div>

          {/* Floating Timeline Panel at Bottom Right */}
          <div className="flex-1 relative flex flex-col justify-end p-4 pointer-events-none overflow-hidden">
            <div className="pointer-events-auto">
              <WeatherTimelinePanel routeData={routeData} forecastTimeline={forecastTimeline} selectedHour={selectedHour} onSelectHour={hour => HOURS.includes(hour) && setSelectedHour(hour)} selectedDay={selectedDay} selectedNodeId={selectedNodeId} onNodeSelect={setSelectedNodeId} activeMode={activeMode} />
            </div>
          </div>
        </div>

        <SafetyAdvisorChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} liveContext={liveContext} activeMode={activeMode} />
      </div>
    </div>
  );
}

export default OperationsDashboard;
