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

import {
  getSafety,
  getForecast,
  getGrid,
  getAdvisories,
  getGeofence,
  getPfzLines,
  getVectorGrid,
  calculateRoute
} from '../services/api';

import {
  MOCK_SAFETY_DATA,
  MOCK_FORECAST_TIMELINE,
  MOCK_GRID_GEOJSON,
  MOCK_ADVISORIES_GEOJSON,
  MOCK_GEOFENCE_GEOJSON,
  MOCK_PFZ_LINES,
  generateMockRoute
} from '../services/mockData';

const VALID_MODES = ['routing', 'fisheries', 'weather'];

/**
 * OperationsDashboard (Smart Parent / State Manager)
 * Central orchestrator for the Navik Naval Operations Console.
 * Manages mode switching (Routing, Fisheries, Weather), MapLibre WebGL canvas,
 * SpotlightCard contextual sidebars, Recharts timeline panel, and Grounded RAG Safety Advisor.
 * Synchronizes with declarative React Router URL parameters and browser history.
 */
export function OperationsDashboard({
  onBackToLanding,
  initialMode = 'routing'
}) {
  const { mode: urlMode } = useParams();
  const navigate = useNavigate();

  // 1. Core Workspace Navigation State (Hydrated from URL params or props)
  const initialResolvedMode = urlMode === 'advisor'
    ? 'routing'
    : (VALID_MODES.includes(urlMode) ? urlMode : (initialMode === 'advisor' ? 'routing' : initialMode || 'routing'));

  const [activeMode, setActiveMode] = useState(initialResolvedMode);
  const [isChatOpen, setIsChatOpen] = useState(urlMode === 'advisor' || initialMode === 'advisor');

  // Synchronize state when browser URL parameter changes (Back/Forward buttons & deep-linking)
  useEffect(() => {
    if (urlMode === 'advisor') {
      setActiveMode('routing');
      setIsChatOpen(true);
    } else if (urlMode && VALID_MODES.includes(urlMode)) {
      setActiveMode(urlMode);
    } else if (urlMode && !VALID_MODES.includes(urlMode)) {
      navigate('/console/routing', { replace: true });
    }
  }, [urlMode, navigate]);

  // Mode switch handler updating browser history via URL
  const handleModeChange = useCallback((newMode) => {
    if (VALID_MODES.includes(newMode)) {
      setActiveMode(newMode);
      navigate(`/console/${newMode}`);
    }
  }, [navigate]);

  // Return to landing page handler
  const handleReturnToLanding = useCallback(() => {
    if (onBackToLanding) {
      onBackToLanding();
    } else {
      navigate('/');
    }
  }, [onBackToLanding, navigate]);

  // 2. Spatial & Hydrodynamic Parameters
  const [selectedLocation, setSelectedLocation] = useState({ lat: 18.9220, lon: 72.8347 }); // Mumbai Port
  const [destinationLocation, setDestinationLocation] = useState({ lat: 10.5667, lon: 72.6417 }); // Lakshadweep (Kavaratti)
  const [beamWidth, setBeamWidth] = useState(3.5);

  // 3. Temporal Forecast Horizon Parameters
  const [selectedDay, setSelectedDay] = useState(1);
  const [selectedHour, setSelectedHour] = useState(12);

  // 4. Data State
  const [safetyData, setSafetyData] = useState(MOCK_SAFETY_DATA);
  const [forecastTimeline, setForecastTimeline] = useState(MOCK_FORECAST_TIMELINE);
  const [routeData, setRouteData] = useState(() => generateMockRoute(
    { lat: 18.9220, lon: 72.8347 },
    { lat: 10.5667, lon: 72.6417 },
    3.5
  ));
  const [gridGeojson, setGridGeojson] = useState(MOCK_GRID_GEOJSON);
  const [advisoriesGeojson, setAdvisoriesGeojson] = useState(MOCK_ADVISORIES_GEOJSON);
  const [geofenceGeojson, setGeofenceGeojson] = useState(MOCK_GEOFENCE_GEOJSON);
  const [pfzGeojson, setPfzGeojson] = useState(MOCK_PFZ_LINES);
  const [vectorGrid, setVectorGrid] = useState({ windGeojson: null, currentGeojson: null });

  // 5. Fisheries & Visual Overlays State
  const [sstOpacity, setSstOpacity] = useState(0.65);
  const [chlOpacity, setChlOpacity] = useState(0.65);
  const [selectedPfz, setSelectedPfz] = useState(null);
  const [layersOverride, setLayersOverride] = useState({});

  // 6. Loading & Async State
  const [isLoading, setIsLoading] = useState(false);
  const [isRouteLoading, setIsRouteLoading] = useState(false);

  // -------------------------------------------------------------
  // Initial Data Fetching & Telemetry Hydration
  // -------------------------------------------------------------
  useEffect(() => {
    let isMounted = true;

    async function loadInitialData() {
      setIsLoading(true);
      try {
        const [grid, adv, geo, pfz, vectors] = await Promise.all([
          getGrid(selectedDay, selectedHour),
          getAdvisories(),
          getGeofence(),
          getPfzLines(),
          getVectorGrid(selectedDay)
        ]);

        if (isMounted) {
          if (grid) setGridGeojson(grid);
          if (adv) setAdvisoriesGeojson(adv);
          if (geo) setGeofenceGeojson(geo);
          if (pfz) setPfzGeojson(pfz);
          if (vectors) setVectorGrid(vectors);
        }
      } catch (err) {
        console.warn('[OperationsDashboard] Error loading initial map data:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadInitialData();

    return () => {
      isMounted = false;
    };
  }, []);

  // -------------------------------------------------------------
  // 1. Fetch New Weather Grid when Time/Day changes
  // -------------------------------------------------------------
  useEffect(() => {
    let isMounted = true;
    async function fetchNewGrid() {
      try {
        const grid = await getGrid(selectedDay, selectedHour);
        if (isMounted && grid) setGridGeojson(grid);
      } catch (err) {
        console.warn('[OperationsDashboard] Error fetching grid:', err);
      }
    }
    fetchNewGrid();
    return () => { isMounted = false; };
  }, [selectedDay, selectedHour]);

  // -------------------------------------------------------------
  // 2. Fetch Forecast Timeline when Location or Day changes
  // -------------------------------------------------------------
  useEffect(() => {
    let isMounted = true;
    async function fetchForecastOnly() {
      if (!selectedLocation?.lat || !selectedLocation?.lon) return;
      try {
        const forecast = await getForecast(selectedLocation.lat, selectedLocation.lon, selectedDay);
        if (isMounted && forecast) setForecastTimeline(forecast);
      } catch (err) {}
    }
    fetchForecastOnly();
    return () => { isMounted = false; };
  }, [selectedLocation, selectedDay]);

  // -------------------------------------------------------------
  // 3. Hydrate Sidebar dynamically when Grid or Location changes
  // -------------------------------------------------------------
  useEffect(() => {
     if (!selectedLocation?.lat || !selectedLocation?.lon || !gridGeojson?.features) return;
     
     let closestFeature = null;
     let minDistance = Infinity;
     
     for (const feature of gridGeojson.features) {
        const props = feature.properties;
        const cLat = props.center_lat ?? feature.geometry.coordinates[0][0][1];
        const cLon = props.center_lon ?? feature.geometry.coordinates[0][0][0];
        const dLat = cLat - selectedLocation.lat;
        const dLon = cLon - selectedLocation.lon;
        const dist = dLat*dLat + dLon*dLon;
        if (dist < minDistance) {
           minDistance = dist;
           closestFeature = feature;
        }
     }
     
     if (closestFeature) {
        const props = closestFeature.properties;
        const bsi = props.bsi || 0;
        const color = props.color || 'green';
        const rating = color === 'red' ? 'DANGER' : color === 'orange' ? 'WARNING' : color === 'yellow' ? 'CAUTION' : 'SAFE';
        
        setSafetyData(prev => ({
          ...prev,
          rating: rating,
          bsi_metrics: { ...prev.bsi_metrics, bsi_score: bsi },
          raw_metrics: {
            ...prev.raw_metrics,
            inspect_hs: props.hs,
            inspect_wind: props.wind_speed_kmh,
            inspect_curr: props.current_speed_ms,
            inspect_mwd: props.wind_dir_deg,
            inspect_hsea: props.hs ? props.hs * 0.7 : 0.8
          }
        }));
     }
  }, [selectedLocation, gridGeojson]);

  // -------------------------------------------------------------
  // Calculate Weather-Optimized A* Safe Route
  // -------------------------------------------------------------
  const handleCalculateRoute = useCallback(async () => {
    if (!selectedLocation || !destinationLocation) return;
    setIsRouteLoading(true);

    try {
      const result = await calculateRoute(
        selectedLocation,
        destinationLocation,
        beamWidth,
        selectedDay,
        selectedHour
      );
      setRouteData(result);
    } catch (err) {
      console.warn('[OperationsDashboard] A* Route calculation fallback engaged:', err);
      setRouteData(generateMockRoute(selectedLocation, destinationLocation, beamWidth));
    } finally {
      setIsRouteLoading(false);
    }
  }, [selectedLocation, destinationLocation, beamWidth, selectedDay, selectedHour]);

  // Clear / Reset Route
  const handleClearRoute = useCallback(() => {
    setRouteData(null);
  }, []);

  // Manual Telemetry Refresh
  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [safety, forecast, grid] = await Promise.all([
        getSafety(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour),
        getForecast(selectedLocation.lat, selectedLocation.lon, selectedDay),
        getGrid(selectedDay, selectedHour)
      ]);
      if (safety) setSafetyData(safety);
      if (forecast) setForecastTimeline(forecast);
      if (grid) setGridGeojson(grid);
    } catch (err) {
      console.warn('[OperationsDashboard] Refresh error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedLocation, beamWidth, selectedDay, selectedHour]);

  // -------------------------------------------------------------
  // Construct Live Context for Grounded RAG Safety Advisor
  // -------------------------------------------------------------
  const overallRisk = routeData?.summary?.overall_risk || safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';
  const maxWave = safetyData?.raw_metrics?.inspect_hs != null 
    ? `${Number(safetyData.raw_metrics.inspect_hs).toFixed(1)}m` 
    : '1.2m';
  const peakWind = safetyData?.raw_metrics?.wind_speed_kmh != null 
    ? `${Number(safetyData.raw_metrics.wind_speed_kmh).toFixed(1)} km/h` 
    : '18.5 km/h';
  const distBorder = safetyData?.raw_metrics?.distance_to_border_km != null 
    ? `${Number(safetyData.raw_metrics.distance_to_border_km).toFixed(1)} km` 
    : '116.9 km (CLEAR)';

  const liveContext = {
    active_workspace: activeMode === 'routing' ? 'Tactical Routing' : activeMode === 'fisheries' ? 'Ocean Analytics' : 'Meteorological Hazards',
    origin_coords: selectedLocation,
    destination_coords: destinationLocation,
    beam_width: `${beamWidth.toFixed(1)}m`,
    current_risk_score: overallRisk,
    bsi_score: safetyData?.bsi_metrics?.bsi_score ?? 1,
    max_wave_height: maxWave,
    wind_speed: peakWind,
    distance_to_border: distBorder,
    avoided_hazards: routeData?.summary?.avoided_hazards || ['Gulf of Mannar MPA', 'High Wave Gradient']
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07111F] text-[#EAF4F8] font-sans overflow-hidden select-none">
      
      {/* 1. Global Naval Top Header HUD */}
      <TopHeader
        activeMode={activeMode}
        selectedLocation={selectedLocation}
        safetyData={safetyData}
        isLoading={isLoading}
        onRefresh={handleRefresh}
        onBackToLanding={handleReturnToLanding}
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
        isChatOpen={isChatOpen}
      />

      {/* 2. Main Workspace: WorkspaceNav Rail + Contextual Sidebar + Map & Timeline */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Far-Left Vertical Icon Rail */}
        <WorkspaceNav
          activeMode={activeMode}
          setActiveMode={handleModeChange}
          onToggleChat={() => setIsChatOpen(!isChatOpen)}
          isChatOpen={isChatOpen}
          onBackToLanding={handleReturnToLanding}
        />

        {/* Contextual SpotlightCard Sidebar */}
        <div className="w-[360px] sm:w-[380px] lg:w-[420px] min-w-[320px] h-full bg-[#0D1B2A] border-r border-[#20384D] flex flex-col shrink-0 z-10">
          <SpotlightCard className="h-full rounded-none border-0 bg-transparent flex flex-col">
            {activeMode === 'routing' && (
              <RoutingSidebar
                selectedLocation={selectedLocation}
                onLocationSelect={setSelectedLocation}
                destinationLocation={destinationLocation}
                onDestinationSelect={setDestinationLocation}
                beamWidth={beamWidth}
                setBeamWidth={setBeamWidth}
                onCalculateRoute={handleCalculateRoute}
                onClearRoute={handleClearRoute}
                routeData={routeData}
                safetyData={safetyData}
                isLoading={isRouteLoading}
              />
            )}

            {activeMode === 'fisheries' && (
              <FisheriesSidebar
                sstOpacity={sstOpacity}
                setSstOpacity={setSstOpacity}
                chlOpacity={chlOpacity}
                setChlOpacity={setChlOpacity}
                pfzList={pfzGeojson?.features || []}
                selectedPfz={selectedPfz}
                onSelectPfz={setSelectedPfz}
                onDestinationSelect={setDestinationLocation}
                selectedLocation={selectedLocation}
                layersOverride={layersOverride}
                setLayersOverride={setLayersOverride}
              />
            )}

            {activeMode === 'weather' && (
              <WeatherSidebar
                selectedDay={selectedDay}
                setSelectedDay={setSelectedDay}
                selectedHour={selectedHour}
                setSelectedHour={setSelectedHour}
                safetyData={safetyData}
                layersOverride={layersOverride}
                setLayersOverride={setLayersOverride}
              />
            )}
          </SpotlightCard>
        </div>

        {/* Center Panel: MapConsole WebGL Engine + Bottom Weather Timeline */}
        <main className="flex-1 flex flex-col h-full bg-[#07111F] relative overflow-hidden">
          
          {/* Interactive WebGL Map Canvas */}
          <div className="flex-1 relative">
            <MapConsole
              activeMode={activeMode}
              selectedLocation={selectedLocation}
              onLocationSelect={setSelectedLocation}
              destinationLocation={destinationLocation}
              onDestinationSelect={setDestinationLocation}
              routeData={routeData}
              pfzGeojson={pfzGeojson}
              advisoriesGeojson={advisoriesGeojson}
              geofenceGeojson={geofenceGeojson}
              gridGeojson={gridGeojson}
              sstOpacity={sstOpacity}
              chlOpacity={chlOpacity}
              beamWidth={beamWidth}
              layersOverride={layersOverride}
              onPfzInspect={(pfzFeature) => {
                setSelectedPfz(pfzFeature);
                if (activeMode !== 'fisheries') {
                  handleModeChange('fisheries');
                }
              }}
            />
          </div>

          {/* Bottom 24-Hour Diurnal Weather Timeline Panel */}
          <WeatherTimelinePanel
            forecastTimeline={forecastTimeline}
            selectedHour={selectedHour}
            onSelectHour={setSelectedHour}
            selectedDay={selectedDay}
          />
        </main>

        {/* 3. Slide-Out Grounded RAG Safety Advisor Drawer */}
        <SafetyAdvisorChat
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          liveContext={liveContext}
          activeMode={activeMode}
        />

      </div>
    </div>
  );
}

export default OperationsDashboard;
