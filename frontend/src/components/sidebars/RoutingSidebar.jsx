import React, { useState, useEffect } from 'react';
import { 
  Navigation, 
  MapPin, 
  Compass, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  Route, 
  ArrowRightLeft, 
  RotateCcw, 
  ChevronRight, 
  Info, 
  Sliders,
  CheckCircle2,
  Sparkles,
  Zap,
  Bell,
  Play,
  Pause,
  Radio
} from 'lucide-react';
import SpotlightCard from '../common/SpotlightCard';
import RiskBadge from '../common/RiskBadge';
import { getNearbyLandingCenters } from '../../services/api';
import { getSeverityBand } from '../../utils/severityBands';

export function RoutingSidebar({
  selectedLocation = { lat: 18.9220, lon: 72.8347 },
  onLocationSelect,
  destinationLocation = null,
  onDestinationSelect,
  vesselProfile = { length_m: 10.0, beam_m: 3.5, cruising_speed_kn: 10.0 },
  setVesselProfile,
  departureTime = new Date().toISOString(),
  setDepartureTime,
  isDepartureManual = false,
  setIsDepartureManual,
  onCalculateRoute,
  onClearRoute,
  routeData = null,
  error = null,
  isLoading = false,
  simulationEnabled = false,
  onSimulationEnabledChange,
  simulationPlaying = false,
  onSimulationPlayingChange,
  simulationSpeed = 1,
  onSimulationSpeedChange,
  onSimulationReset,
  boundaryAlert = null,
  routeAheadAlert = null,
  simulationNodeIndex = 0,
  simulationProgress = 0,
  notificationPermission = 'default',
  onRequestBrowserNotifications
}) {
  const [selectedOriginPort, setSelectedOriginPort] = useState('');
  const [selectedDestPort, setSelectedDestPort] = useState('');
  const [landingCenters, setLandingCenters] = useState([]);

  useEffect(() => {
    getNearbyLandingCenters((selectedLocation?.lat) || 18.9220, (selectedLocation?.lon) || 72.8347)
      .then(setLandingCenters)
      .catch(console.error);
  }, [(selectedLocation?.lat), (selectedLocation?.lon)]);

  const handleOriginPortChange = (e) => {
    const portId = e.target.value;
    setSelectedOriginPort(portId);
    const port = landingCenters.find(p => p.id === portId);
    if (port && onLocationSelect) {
      onLocationSelect({ lat: port.lat, lon: port.lon });
    }
  };

  const handleDestPortChange = (e) => {
    const portId = e.target.value;
    setSelectedDestPort(portId);
    const port = landingCenters.find(p => p.id === portId);
    if (port && onDestinationSelect) {
      onDestinationSelect({ lat: port.lat, lon: port.lon });
    }
  };

  const handleSwapPorts = () => {
    if (!destinationLocation) return;
    const temp = { ...selectedLocation };
    if (onLocationSelect) onLocationSelect(destinationLocation);
    if (onDestinationSelect) onDestinationSelect(temp);
    const tempPort = selectedOriginPort;
    setSelectedOriginPort(selectedDestPort);
    setSelectedDestPort(tempPort);
  };

  const alertTheme = {
    SAFE: 'border-[#18C7A0]/35 bg-[#18C7A0]/10 text-[#18C7A0]',
    WATCH: 'border-[#00D4FF]/35 bg-[#00D4FF]/10 text-[#00D4FF]',
    WARNING: 'border-[#FFB547]/35 bg-[#FFB547]/10 text-[#FFB547]',
    DANGER: 'border-[#FF5C5C]/35 bg-[#FF5C5C]/10 text-[#FF5C5C]',
    UNAVAILABLE: 'border-[#8FA8B8]/35 bg-[#8FA8B8]/10 text-[#8FA8B8]'
  };
  const activeAlert = boundaryAlert || { level: 'SAFE', boundaryName: 'known EEZ / MPA boundaries', instruction: 'Enable the simulator to evaluate a demo vessel position.' };
  const formatDistance = distance => Number.isFinite(Number(distance)) ? `${Number(distance).toFixed(1)} km` : 'Not available';
  const formatEta = eta => {
    if (!eta) return null;
    const value = new Date(eta);
    return Number.isNaN(value.getTime()) ? null : value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <aside className="w-full h-full flex flex-col justify-between overflow-y-auto p-4 space-y-4 select-none font-sans text-xs">
      <div className="space-y-4">
        
        {/* 1. Header Banner */}
        <div className="flex items-center justify-between border-b border-[#20384D] pb-2.5">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-[#00D4FF]" />
            <h2 className="font-mono font-bold text-sm text-[#EAF4F8] uppercase tracking-wider">
              Tactical Routing (A*)
            </h2>
          </div>
          <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30">
            MODE A
          </span>
        </div>

        {/* 2. Waypoint Coordinates & Port Selection Card */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase">
              Voyage Terminals
            </span>
            <button
              onClick={handleSwapPorts}
              disabled={!destinationLocation}
              className="p-1 rounded bg-[#0D1B2A] hover:bg-[#1b344e] text-[#00D4FF] border border-[#20384D] transition disabled:opacity-40 cursor-pointer"
              title="Swap Origin & Destination"
            >
              <ArrowRightLeft className="w-3 h-3" />
            </button>
          </div>

          {/* Origin Selector */}
          <div className="space-y-1.5">
            <label className="text-[9px] text-[#8FA8B8] font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#18C7A0]" />
              Origin (Departure Port / Vessel Pin)
            </label>
            <select
              value={selectedOriginPort}
              onChange={handleOriginPortChange}
              className="w-full bg-[#07111F] border border-[#20384D] rounded-lg px-2.5 py-1.5 text-xs text-[#EAF4F8] font-mono focus:border-[#00D4FF] focus:outline-none"
            >
              <option value="">-- Custom Coordinates --</option>
              {landingCenters.map(port => (
                <option key={port.id} value={port.id}>
                  {port.name}, {port.district} ({port.lat.toFixed(2)}°N, {port.lon.toFixed(2)}°E)
                </option>
              ))}
            </select>
            <div className="flex gap-2 text-[10px] font-mono text-[#8FA8B8]">
              <span>Lat: <strong className="text-[#EAF4F8]">{selectedLocation?.lat?.toFixed(4) ?? '—'}°</strong></span>
              <span>Lon: <strong className="text-[#EAF4F8]">{selectedLocation?.lon?.toFixed(4) ?? '—'}°</strong></span>
            </div>
          </div>

          {/* Destination Selector */}
          <div className="space-y-1.5 pt-1 border-t border-[#20384D]/60">
            <label className="text-[9px] text-[#8FA8B8] font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#FF5C5C]" />
              Destination (Target Port / Draggable Pin)
            </label>
            <select
              value={selectedDestPort}
              onChange={handleDestPortChange}
              className="w-full bg-[#07111F] border border-[#20384D] rounded-lg px-2.5 py-1.5 text-xs text-[#EAF4F8] font-mono focus:border-[#00D4FF] focus:outline-none"
            >
              <option value="">-- Drag White Pin on Map or Select --</option>
              {landingCenters.map(port => (
                <option key={port.id} value={port.id}>
                  {port.name}, {port.district} ({port.lat.toFixed(2)}°N, {port.lon.toFixed(2)}°E)
                </option>
              ))}
            </select>
            <div className="flex gap-2 text-[10px] font-mono text-[#8FA8B8]">
              <span>Lat: <strong className="text-[#EAF4F8]">{destinationLocation?.lat?.toFixed(4) ?? 'Not Set'}</strong></span>
              <span>Lon: <strong className="text-[#EAF4F8]">{destinationLocation?.lon?.toFixed(4) ?? 'Not Set'}</strong></span>
            </div>
          </div>
        </SpotlightCard>

        {/* 3. Vessel Hydrodynamics & Constraints */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase">
              Vessel Profile & Time
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div className="space-y-1">
              <label className="text-[#8FA8B8]">Length (m)</label>
              <input
                type="number" step="0.1"
                value={vesselProfile?.length_m || 10.0}
                onChange={e => setVesselProfile && setVesselProfile({...vesselProfile, length_m: parseFloat(e.target.value)})}
                className="w-full bg-[#07111F] border border-[#20384D] rounded px-2 py-1 text-[#EAF4F8]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[#8FA8B8]">Beam (m)</label>
              <input
                type="number" step="0.1"
                value={vesselProfile?.beam_m || 3.5}
                onChange={e => setVesselProfile && setVesselProfile({...vesselProfile, beam_m: parseFloat(e.target.value)})}
                className="w-full bg-[#07111F] border border-[#20384D] rounded px-2 py-1 text-[#EAF4F8]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[#8FA8B8]">Speed (knots)</label>
              <input
                type="number" step="0.5"
                value={vesselProfile?.cruising_speed_kn || 10.0}
                onChange={e => setVesselProfile && setVesselProfile({...vesselProfile, cruising_speed_kn: parseFloat(e.target.value)})}
                className="w-full bg-[#07111F] border border-[#20384D] rounded px-2 py-1 text-[#EAF4F8]"
              />
            </div>
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className="text-[#8FA8B8]">Departure</label>
                <button 
                  type="button"
                  onClick={() => {
                    if (setIsDepartureManual) setIsDepartureManual(false);
                    if (setDepartureTime) setDepartureTime(new Date().toISOString());
                  }} 
                  className="text-[#00D4FF] hover:text-[#EAF4F8] text-[9px] uppercase font-bold cursor-pointer"
                >
                  [ Now ]
                </button>
              </div>
              <input
                type="datetime-local"
                value={departureTime ? (() => {
                  const d = new Date(departureTime);
                  if (isNaN(d.getTime())) return '';
                  const pad = n => n.toString().padStart(2, '0');
                  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
                })() : ''}
                onChange={e => {
                  if (setIsDepartureManual) setIsDepartureManual(true);
                  if (setDepartureTime) {
                    if (!e.target.value) {
                      setDepartureTime(null);
                    } else {
                      const d = new Date(e.target.value);
                      if (!isNaN(d.getTime())) {
                        setDepartureTime(d.toISOString());
                      }
                    }
                  }
                }}
                className="w-full bg-[#07111F] border border-[#20384D] rounded px-2 py-1 text-[#EAF4F8]"
              />
            </div>
          </div>
        </SpotlightCard>

        {/* 4. Action CTA: Calculate Safe Route */}
        <div className="space-y-2">
          {error && (
            <div className="p-2.5 rounded bg-[#FF5C5C]/10 border border-[#FF5C5C]/30 text-[#FF5C5C] text-[10px] font-mono text-center">
              {typeof error === 'string' ? error : "Marine forecast unavailable — route could not be evaluated"}
            </div>
          )}

          <button
            type="button"
            onClick={onCalculateRoute}
            disabled={isLoading || !destinationLocation}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#00D4FF] to-[#0099CC] hover:from-[#33DDFF] hover:to-[#00B4D8] text-[#07111F] font-mono font-black text-[10px] sm:text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-[0_0_18px_rgba(0,212,255,0.35)] transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin text-[#07111F]" />
                <span>CALCULATING RECOMMENDED ROUTE...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-current" />
                <span>Calculate Recommended Route</span>
              </>
            )}
          </button>

          {routeData && (
            <button
              type="button"
              onClick={onClearRoute}
              className="w-full py-1.5 px-3 rounded-lg bg-[#0D1B2A] hover:bg-[#13263A] border border-[#20384D] text-[#8FA8B8] hover:text-[#EAF4F8] font-mono text-[10px] transition cursor-pointer flex items-center justify-center gap-1.5"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset Planned Trajectory</span>
            </button>
          )}
        </div>

        {/* 5. Planned Route KPI Summary Card */}
        {routeData && !isLoading && (
          <SpotlightCard className="p-3.5 space-y-3 border-[#00D4FF]/40">
            <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
              <span className="text-[10px] font-mono font-bold text-[#00D4FF] uppercase flex items-center gap-1.5">
                <Route className="w-3.5 h-3.5" />
                Route Execution Plan
              </span>
            </div>

            <div className="text-[10px] font-mono text-center p-2 rounded bg-[#18C7A0]/10 border border-[#18C7A0]/30 text-[#18C7A0]">
              ORCA recommends this route — predicted peak severity {routeData?.optimization?.selected_route_peak_severity || 0}/100
            </div>

            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
                <span className="text-[8px] text-[#8FA8B8] uppercase block">Total Distance</span>
                <span className="text-xs font-mono font-bold text-[#EAF4F8] mt-0.5 block">
                  {routeData?.route?.distance_km} km
                </span>
              </div>
              <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
                <span className="text-[8px] text-[#8FA8B8] uppercase block">Est. Duration</span>
                <span className="text-xs font-mono font-bold text-[#00D4FF] mt-0.5 block">
                  {routeData?.route?.duration_hours} hrs
                </span>
              </div>
            </div>
            
            {routeData?.optimization && (
              <div className="text-[9px] text-[#8FA8B8] space-y-1 bg-[#07111F] p-2 rounded border border-[#20384D]">
                <div>Shortest path peak severity: <strong className="text-[#FFB547]">{routeData.optimization.shortest_route_peak_severity}</strong></div>
                <div>Extra distance taken: <strong>{routeData.optimization.additional_distance_km} km</strong></div>
              </div>
            )}
            
          </SpotlightCard>
        )}

        {/* 6. Demo Vessel Simulator and known-boundary watch */}
        <SpotlightCard className="p-3.5 space-y-3 border-[#00D4FF]/30">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#00D4FF] uppercase flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5" />
              Demo Vessel Simulator
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={simulationEnabled}
              onClick={() => onSimulationEnabledChange?.(!simulationEnabled)}
              className={`rounded px-2 py-1 text-[9px] font-mono font-bold uppercase border transition ${simulationEnabled ? 'border-[#00D4FF]/60 bg-[#00D4FF]/15 text-[#00D4FF]' : 'border-[#20384D] bg-[#07111F] text-[#8FA8B8]'}`}
            >
              {simulationEnabled ? 'Enabled' : 'Enable'}
            </button>
          </div>

          <p className="rounded border border-[#FFB547]/25 bg-[#FFB547]/5 px-2 py-1.5 text-[9px] leading-relaxed text-[#FFB547]">
            Demo Simulation — map position only, not live GPS/AIS telemetry.
          </p>

          <div className={`rounded-lg border p-2.5 ${alertTheme[activeAlert.level] || alertTheme.UNAVAILABLE}`}>
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-[10px] font-bold uppercase">Boundary Watch · {activeAlert.level}</span>
              {simulationEnabled && <span className="font-mono text-[9px]">Node {simulationNodeIndex + 1}</span>}
            </div>
            <p className="mt-1.5 text-[10px] font-semibold">{activeAlert.boundaryName}</p>
            {activeAlert.level !== 'UNAVAILABLE' && simulationEnabled && <p className="mt-0.5 text-[9px] opacity-85">Nearest known boundary: {formatDistance(activeAlert.distanceKm)}</p>}
            <p className="mt-1.5 text-[10px] leading-relaxed text-[#EAF4F8]">{activeAlert.instruction}</p>
            {activeAlert.reason && <p className="mt-1 text-[9px] opacity-85">{activeAlert.reason}</p>}
          </div>

          {routeAheadAlert && (
            <div className="rounded border border-[#FFB547]/30 bg-[#07111F] p-2 text-[9px] text-[#EAF4F8]">
              <span className="font-mono font-bold uppercase text-[#FFB547]">Route-ahead watch</span>
              <p className="mt-1">{routeAheadAlert.boundaryName} · {formatDistance(routeAheadAlert.distanceKm)}{formatEta(routeAheadAlert.routeNode?.eta) ? ` · ETA ${formatEta(routeAheadAlert.routeNode.eta)}` : ''}</p>
            </div>
          )}

          <div className="grid grid-cols-3 gap-1.5">
            <button type="button" disabled={!simulationEnabled || !routeData?.path?.length || simulationPlaying} onClick={() => onSimulationPlayingChange?.(true)} className="rounded border border-[#20384D] bg-[#07111F] px-2 py-1.5 text-[9px] font-mono text-[#EAF4F8] disabled:opacity-40"><Play className="mr-1 inline h-3 w-3" />Play</button>
            <button type="button" disabled={!simulationEnabled || !simulationPlaying} onClick={() => onSimulationPlayingChange?.(false)} className="rounded border border-[#20384D] bg-[#07111F] px-2 py-1.5 text-[9px] font-mono text-[#EAF4F8] disabled:opacity-40"><Pause className="mr-1 inline h-3 w-3" />Pause</button>
            <button type="button" disabled={!simulationEnabled} onClick={onSimulationReset} className="rounded border border-[#20384D] bg-[#07111F] px-2 py-1.5 text-[9px] font-mono text-[#EAF4F8] disabled:opacity-40"><RotateCcw className="mr-1 inline h-3 w-3" />Reset</button>
          </div>

          <div className="flex items-center justify-between gap-2 text-[9px] text-[#8FA8B8]">
            <span>Playback</span>
            <div className="flex gap-1">{[1, 5, 20].map(speed => <button key={speed} type="button" disabled={!simulationEnabled} onClick={() => onSimulationSpeedChange?.(speed)} className={`rounded border px-1.5 py-0.5 font-mono disabled:opacity-40 ${simulationSpeed === speed ? 'border-[#00D4FF]/60 bg-[#00D4FF]/15 text-[#00D4FF]' : 'border-[#20384D] text-[#8FA8B8]'}`}>{speed}×</button>)}</div>
          </div>
          {simulationEnabled && routeData?.path?.length > 1 && <div className="h-1 overflow-hidden rounded bg-[#07111F]"><div className="h-full bg-[#00D4FF] transition-[width]" style={{ width: `${Math.min(100, (simulationProgress / (routeData.path.length - 1)) * 100)}%` }} /></div>}

          <button type="button" onClick={onRequestBrowserNotifications} disabled={notificationPermission === 'granted' || notificationPermission === 'unsupported'} className="w-full rounded border border-[#20384D] bg-[#07111F] px-2 py-1.5 text-[9px] font-mono text-[#8FA8B8] hover:text-[#EAF4F8] disabled:opacity-50">
            <Bell className="mr-1 inline h-3 w-3" />
            {notificationPermission === 'granted' ? 'Browser boundary alerts enabled' : notificationPermission === 'denied' ? 'Browser alerts blocked — in-app alerts remain active' : notificationPermission === 'unsupported' ? 'Browser alerts unsupported — in-app alerts remain active' : 'Enable browser boundary alerts'}
          </button>
        </SpotlightCard>

      </div>

      {/* Footer System Stamp */}
      <div className="pt-2 border-t border-[#20384D] text-[9px] text-[#8FA8B8] flex justify-between font-mono">
        <span>A* PostGIS Solver</span>
        <span>ORCA v2.3 Validated</span>
      </div>
    </aside>
  );
}

export default RoutingSidebar;
