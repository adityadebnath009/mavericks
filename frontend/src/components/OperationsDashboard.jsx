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

const VALID_MODES = ['routing', 'fisheries', 'weather'];
const HOURS = [0, 3, 6, 9, 12, 15, 18, 21];

const INITIAL_LOCATION = { lat: 18.9220, lon: 72.8347 };
const INITIAL_DESTINATION = { lat: 10.5667, lon: 72.6417 };

const INITIAL_STATUS = {
  safety: 'loading',
  forecast: 'loading',
  grid: 'loading',
  vectors: 'loading',
  advisories: 'loading',
  geofence: 'loading',
  pfz: 'loading'
};

const emptyVectorGrid = { windGeojson: null, currentGeojson: null, timestamp: null };

function classifyPayload(payload) {
  const source = String(
    payload?.source || payload?.provenance?.source || payload?.metadata?.source || ''
  ).toLowerCase();

  if (source.includes('cache')) return 'cached';
  if (source.includes('fallback') || source.includes('open-meteo') || source.includes('mock')) return 'cached';
  return 'live';
}

function classifyError() {
  return 'unavailable';
}

function resultOf(promise) {
  return promise
    .then(data => ({ ok: true, data }))
    .catch(error => ({ ok: false, error }));
}

export function OperationsDashboard({ onBackToLanding, initialMode = 'routing' }) {
  const { mode: urlMode } = useParams();
  const navigate = useNavigate();

  const initialResolvedMode = urlMode === 'advisor'
    ? 'routing'
    : (VALID_MODES.includes(urlMode) ? urlMode : (initialMode === 'advisor' ? 'routing' : initialMode || 'routing'));

  const [activeMode, setActiveMode] = useState(initialResolvedMode);
  const [isChatOpen, setIsChatOpen] = useState(urlMode === 'advisor' || initialMode === 'advisor');

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

  const handleModeChange = useCallback((newMode) => {
    if (VALID_MODES.includes(newMode)) {
      setActiveMode(newMode);
      navigate(`/console/${newMode}`);
    }
  }, [navigate]);

  const handleReturnToLanding = useCallback(() => {
    if (onBackToLanding) onBackToLanding();
    else navigate('/');
  }, [onBackToLanding, navigate]);

  const [selectedLocation, setSelectedLocation] = useState(INITIAL_LOCATION);
  const [destinationLocation, setDestinationLocation] = useState(INITIAL_DESTINATION);
  const [beamWidth, setBeamWidth] = useState(3.5);
  const [selectedDay, setSelectedDay] = useState(1);
  const [selectedHour, setSelectedHour] = useState(12);

  const [safetyData, setSafetyData] = useState(null);
  const [forecastTimeline, setForecastTimeline] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [gridGeojson, setGridGeojson] = useState(null);
  const [advisoriesGeojson, setAdvisoriesGeojson] = useState(null);
  const [geofenceGeojson, setGeofenceGeojson] = useState(null);
  const [pfzGeojson, setPfzGeojson] = useState(null);
  const [vectorGrid, setVectorGrid] = useState(emptyVectorGrid);
  const [dataStatus, setDataStatus] = useState(INITIAL_STATUS);

  const [sstOpacity, setSstOpacity] = useState(0.65);
  const [chlOpacity, setChlOpacity] = useState(0.65);
  const [selectedPfz, setSelectedPfz] = useState(null);
  const [layersOverride, setLayersOverride] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRouteLoading, setIsRouteLoading] = useState(false);

  // Authoritative safety state: exact selected location + selected day/hour.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, safety: 'loading' }));

    resultOf(getSafety(
      selectedLocation.lat,
      selectedLocation.lon,
      beamWidth,
      selectedDay,
      selectedHour
    )).then(result => {
      if (!active) return;
      if (result.ok) {
        setSafetyData(result.data);
        setDataStatus(prev => ({ ...prev, safety: classifyPayload(result.data) }));
      } else {
        setDataStatus(prev => ({ ...prev, safety: classifyError() }));
      }
    });

    return () => { active = false; };
  }, [selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour]);

  // Location/day-sensitive 24-hour forecast.
  useEffect(() => {
    let active = true;
    if (selectedLocation?.lat == null || selectedLocation?.lon == null) return () => { active = false; };
    setDataStatus(prev => ({ ...prev, forecast: 'loading' }));

    resultOf(getForecast(selectedLocation.lat, selectedLocation.lon, selectedDay)).then(result => {
      if (!active) return;
      if (result.ok) {
        setForecastTimeline(result.data);
        setDataStatus(prev => ({ ...prev, forecast: classifyPayload(result.data) }));
      } else {
        setDataStatus(prev => ({ ...prev, forecast: classifyError() }));
      }
    });

    return () => { active = false; };
  }, [selectedLocation.lat, selectedLocation.lon, selectedDay]);

  // Exact temporal synchronization: BSI grid + wind/current vectors use the same day/hour.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, grid: 'loading', vectors: 'loading' }));

    Promise.all([
      resultOf(getGrid(selectedDay, selectedHour)),
      resultOf(getVectorGrid(selectedDay, selectedHour))
    ]).then(([gridResult, vectorResult]) => {
      if (!active) return;

      if (gridResult.ok) {
        setGridGeojson(gridResult.data);
        setDataStatus(prev => ({ ...prev, grid: classifyPayload(gridResult.data) }));
      } else {
        setDataStatus(prev => ({ ...prev, grid: classifyError() }));
      }

      if (vectorResult.ok) {
        setVectorGrid(vectorResult.data);
        setDataStatus(prev => ({ ...prev, vectors: classifyPayload(vectorResult.data) }));
      } else {
        setVectorGrid(emptyVectorGrid);
        setDataStatus(prev => ({ ...prev, vectors: classifyError() }));
      }
    });

    return () => { active = false; };
  }, [selectedDay, selectedHour]);

  // Location-independent operational overlays are loaded once and refreshed explicitly.
  useEffect(() => {
    let active = true;
    setDataStatus(prev => ({ ...prev, advisories: 'loading', geofence: 'loading', pfz: 'loading' }));

    Promise.all([
      resultOf(getAdvisories()),
      resultOf(getGeofence()),
      resultOf(getPfzLines())
    ]).then(([adv, geo, pfz]) => {
      if (!active) return;

      if (adv.ok) {
        setAdvisoriesGeojson(adv.data);
        setDataStatus(prev => ({ ...prev, advisories: classifyPayload(adv.data) }));
      } else setDataStatus(prev => ({ ...prev, advisories: classifyError() }));

      if (geo.ok) {
        setGeofenceGeojson(geo.data);
        setDataStatus(prev => ({ ...prev, geofence: classifyPayload(geo.data) }));
      } else setDataStatus(prev => ({ ...prev, geofence: classifyError() }));

      if (pfz.ok) {
        setPfzGeojson(pfz.data);
        setDataStatus(prev => ({ ...prev, pfz: classifyPayload(pfz.data) }));
      } else setDataStatus(prev => ({ ...prev, pfz: classifyError() }));
    });

    return () => { active = false; };
  }, []);

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
      console.warn('[OperationsDashboard] Route unavailable:', err);
      setRouteData(null);
    } finally {
      setIsRouteLoading(false);
    }
  }, [selectedLocation, destinationLocation, beamWidth, selectedDay, selectedHour]);

  const handleClearRoute = useCallback(() => setRouteData(null), []);

  // One explicit global refresh: all seven dynamic datasets are fired together.
  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    setDataStatus({
      safety: 'loading',
      forecast: 'loading',
      grid: 'loading',
      vectors: 'loading',
      advisories: 'loading',
      geofence: 'loading',
      pfz: 'loading'
    });

    const results = await Promise.all([
      resultOf(getSafety(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour)),
      resultOf(getForecast(selectedLocation.lat, selectedLocation.lon, selectedDay)),
      resultOf(getGrid(selectedDay, selectedHour)),
      resultOf(getVectorGrid(selectedDay, selectedHour)),
      resultOf(getAdvisories()),
      resultOf(getGeofence()),
      resultOf(getPfzLines())
    ]);

    const [safety, forecast, grid, vectors, advisories, geofence, pfz] = results;

    if (safety.ok) setSafetyData(safety.data);
    if (forecast.ok) setForecastTimeline(forecast.data);
    if (grid.ok) setGridGeojson(grid.data);
    if (vectors.ok) setVectorGrid(vectors.data);
    else setVectorGrid(emptyVectorGrid);
    if (advisories.ok) setAdvisoriesGeojson(advisories.data);
    if (geofence.ok) setGeofenceGeojson(geofence.data);
    if (pfz.ok) setPfzGeojson(pfz.data);

    setDataStatus({
      safety: safety.ok ? classifyPayload(safety.data) : classifyError(),
      forecast: forecast.ok ? classifyPayload(forecast.data) : classifyError(),
      grid: grid.ok ? classifyPayload(grid.data) : classifyError(),
      vectors: vectors.ok ? classifyPayload(vectors.data) : classifyError(),
      advisories: advisories.ok ? classifyPayload(advisories.data) : classifyError(),
      geofence: geofence.ok ? classifyPayload(geofence.data) : classifyError(),
      pfz: pfz.ok ? classifyPayload(pfz.data) : classifyError()
    });

    setIsLoading(false);
  }, [selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour]);

  const overallRisk = routeData?.summary?.overall_risk || safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';
  const maxWave = safetyData?.raw_metrics?.inspect_hs != null ? `${Number(safetyData.raw_metrics.inspect_hs).toFixed(1)}m` : 'N/A';
  const peakWind = safetyData?.raw_metrics?.wind_speed_kmh != null ? `${Number(safetyData.raw_metrics.wind_speed_kmh).toFixed(1)} km/h` : 'N/A';
  const distBorder = safetyData?.raw_metrics?.distance_to_border_km != null ? `${Number(safetyData.raw_metrics.distance_to_border_km).toFixed(1)} km` : 'N/A';

  const liveContext = {
    active_workspace: activeMode === 'routing' ? 'Tactical Routing' : activeMode === 'fisheries' ? 'Ocean Analytics' : 'Meteorological Hazards',
    origin_coords: selectedLocation,
    destination_coords: destinationLocation,
    beam_width: `${beamWidth.toFixed(1)}m`,
    current_risk_score: overallRisk,
    bsi_score: safetyData?.bsi_metrics?.bsi_score ?? null,
    max_wave_height: maxWave,
    wind_speed: peakWind,
    distance_to_border: distBorder,
    avoided_hazards: routeData?.summary?.avoided_hazards || []
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07111F] text-[#EAF4F8] font-sans overflow-hidden select-none">
      <TopHeader
        activeMode={activeMode}
        selectedLocation={selectedLocation}
        safetyData={safetyData}
        dataStatus={dataStatus}
        isLoading={isLoading}
        onRefresh={handleRefresh}
        onBackToLanding={handleReturnToLanding}
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
        isChatOpen={isChatOpen}
      />

      <div className="flex flex-1 overflow-hidden relative">
        <WorkspaceNav
          activeMode={activeMode}
          setActiveMode={handleModeChange}
          onToggleChat={() => setIsChatOpen(!isChatOpen)}
          isChatOpen={isChatOpen}
          onBackToLanding={handleReturnToLanding}
        />

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
                setSelectedHour={(hour) => HOURS.includes(hour) && setSelectedHour(hour)}
                safetyData={safetyData}
                layersOverride={layersOverride}
                setLayersOverride={setLayersOverride}
              />
            )}
          </SpotlightCard>
        </div>

        <main className="flex-1 flex flex-col h-full bg-[#07111F] relative overflow-hidden">
          <div className="flex-1 relative">
            <MapConsole
              activeMode={activeMode}
              selectedLocation={selectedLocation}
              onLocationSelect={setSelectedLocation}
              destinationLocation={destinationLocation}
              onDestinationSelect={setDestinationLocation}
              routeData={routeData}
              pfzGeojson={pfzGeojson}
              vectorGrid={vectorGrid}
              advisoriesGeojson={advisoriesGeojson}
              geofenceGeojson={geofenceGeojson}
              gridGeojson={gridGeojson}
              sstOpacity={sstOpacity}
              chlOpacity={chlOpacity}
              beamWidth={beamWidth}
              layersOverride={layersOverride}
              onPfzInspect={(pfzFeature) => {
                setSelectedPfz(pfzFeature);
                if (activeMode !== 'fisheries') handleModeChange('fisheries');
              }}
            />
          </div>

          <WeatherTimelinePanel
            forecastTimeline={forecastTimeline}
            selectedHour={selectedHour}
            onSelectHour={(hour) => HOURS.includes(hour) && setSelectedHour(hour)}
            selectedDay={selectedDay}
          />
        </main>

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
