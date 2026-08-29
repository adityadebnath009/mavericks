import React, { useState } from 'react';
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
  Zap
} from 'lucide-react';
import SpotlightCard from '../common/SpotlightCard';
import RiskBadge from '../common/RiskBadge';
import { MOCK_PORTS } from '../../services/mockData';

export function RoutingSidebar({
  selectedLocation = { lat: 18.9220, lon: 72.8347 },
  onLocationSelect,
  destinationLocation = null,
  onDestinationSelect,
  beamWidth = 3.5,
  setBeamWidth,
  onCalculateRoute,
  onClearRoute,
  routeData = null,
  safetyData = null,
  isLoading = false
}) {
  const [selectedOriginPort, setSelectedOriginPort] = useState('mumbai');
  const [selectedDestPort, setSelectedDestPort] = useState('');

  const handleOriginPortChange = (e) => {
    const portId = e.target.value;
    setSelectedOriginPort(portId);
    const port = MOCK_PORTS.find(p => p.id === portId);
    if (port && onLocationSelect) {
      onLocationSelect({ lat: port.lat, lon: port.lon });
    }
  };

  const handleDestPortChange = (e) => {
    const portId = e.target.value;
    setSelectedDestPort(portId);
    const port = MOCK_PORTS.find(p => p.id === portId);
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

  const overallRisk = routeData?.summary?.overall_risk || safetyData?.rating || 'LOW';
  const isVulnerable = beamWidth < 4.0 && safetyData?.vessel_suitability?.vulnerable;

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
              {MOCK_PORTS.map(port => (
                <option key={port.id} value={port.id}>
                  {port.name} ({port.lat.toFixed(2)}°N, {port.lon.toFixed(2)}°E)
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
              {MOCK_PORTS.map(port => (
                <option key={port.id} value={port.id}>
                  {port.name} ({port.lat.toFixed(2)}°N, {port.lon.toFixed(2)}°E)
                </option>
              ))}
            </select>
            <div className="flex gap-2 text-[10px] font-mono text-[#8FA8B8]">
              <span>Lat: <strong className="text-[#EAF4F8]">{destinationLocation?.lat?.toFixed(4) ?? 'Not Set'}</strong></span>
              <span>Lon: <strong className="text-[#EAF4F8]">{destinationLocation?.lon?.toFixed(4) ?? 'Not Set'}</strong></span>
            </div>
          </div>
        </SpotlightCard>

        {/* 3. Vessel Stability & Beam Width Card */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase">
              Vessel Hydrodynamics
            </span>
            {isVulnerable ? (
              <span className="text-[8px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#FF5C5C]/20 text-[#FF5C5C] border border-[#FF5C5C]/40 animate-pulse">
                SVAS VULNERABLE
              </span>
            ) : (
              <span className="text-[8px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#18C7A0]/20 text-[#18C7A0] border border-[#18C7A0]/40">
                STABLE HULL
              </span>
            )}
          </div>

          {/* Suffix Buttons */}
          <div className="flex gap-2">
            {[
              { label: '< 4m Small Craft', val: 3.5 },
              { label: '< 6m Trawler', val: 5.0 },
              { label: '< 7m Deep-Sea', val: 6.5 }
            ].map(item => (
              <button
                key={item.val}
                type="button"
                onClick={() => setBeamWidth && setBeamWidth(item.val)}
                className={`flex-1 py-1.5 rounded-lg border font-mono text-[9px] font-bold transition cursor-pointer text-center ${
                  (item.val === 3.5 && beamWidth < 4.0) ||
                  (item.val === 5.0 && beamWidth >= 4.0 && beamWidth < 6.0) ||
                  (item.val === 6.5 && beamWidth >= 6.0)
                    ? 'bg-[#00D4FF]/20 border-[#00D4FF] text-[#00D4FF] shadow-[0_0_10px_rgba(0,212,255,0.2)]'
                    : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:text-[#EAF4F8]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Precision Slider */}
          <div className="space-y-1">
            <div className="flex justify-between text-[9px] font-mono text-[#8FA8B8]">
              <span>Beam Width: <strong className="text-[#00D4FF]">{beamWidth.toFixed(1)}m</strong></span>
              <span>Range: 1.0m — 8.0m</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="8.0"
              step="0.1"
              value={beamWidth}
              onChange={(e) => setBeamWidth && setBeamWidth(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-[#07111F] rounded-lg appearance-none cursor-pointer accent-[#00D4FF]"
            />
          </div>
        </SpotlightCard>

        {/* 4. Action CTA: Calculate Safe Route */}
        <div className="space-y-2">
          <button
            type="button"
            onClick={onCalculateRoute}
            disabled={isLoading || !destinationLocation}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#00D4FF] to-[#0099CC] hover:from-[#33DDFF] hover:to-[#00B4D8] text-[#07111F] font-mono font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-[0_0_18px_rgba(0,212,255,0.35)] transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin text-[#07111F]" />
                <span>Running A* Pathfinding...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-current" />
                <span>Calculate Safe Route (A*)</span>
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
        {routeData && routeData.summary && (
          <SpotlightCard className="p-3.5 space-y-3 border-[#00D4FF]/40">
            <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
              <span className="text-[10px] font-mono font-bold text-[#00D4FF] uppercase flex items-center gap-1.5">
                <Route className="w-3.5 h-3.5" />
                Route Execution Plan
              </span>
              <RiskBadge level={routeData.summary.overall_risk || overallRisk} size="xs" />
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
                <span className="text-[8px] text-[#8FA8B8] uppercase block">Total Distance</span>
                <span className="text-xs font-mono font-bold text-[#EAF4F8] mt-0.5 block">
                  {routeData.summary.distance_km} km
                </span>
                <span className="text-[7.5px] text-[#8FA8B8] font-mono">
                  ({routeData.summary.distance_nmi ?? (routeData.summary.distance_km / 1.852).toFixed(1)} nmi)
                </span>
              </div>

              <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
                <span className="text-[8px] text-[#8FA8B8] uppercase block">Est. Duration</span>
                <span className="text-xs font-mono font-bold text-[#00D4FF] mt-0.5 block">
                  {routeData.summary.travel_time_hours} hrs
                </span>
                <span className="text-[7.5px] text-[#8FA8B8] font-mono">@ 10 knots</span>
              </div>

              <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
                <span className="text-[8px] text-[#8FA8B8] uppercase block">Peak BSI</span>
                <span className="text-xs font-mono font-bold text-[#18C7A0] mt-0.5 block">
                  {routeData.summary.max_bsi ?? 1} / 7
                </span>
                <span className="text-[7.5px] text-[#18C7A0] font-mono">Safe</span>
              </div>
            </div>

            {/* Avoided Hazards List */}
            {routeData.summary.avoided_hazards?.length > 0 && (
              <div className="space-y-1.5 pt-1 border-t border-[#20384D]/60">
                <span className="text-[9px] font-mono font-bold text-[#8FA8B8] uppercase block">
                  Geofenced Mitigations:
                </span>
                <div className="space-y-1">
                  {routeData.summary.avoided_hazards.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 text-[9px] text-[#8FA8B8]">
                      <CheckCircle2 className="w-3 h-3 text-[#18C7A0] shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Straight vs Optimized Comparison */}
            {routeData.comparison && (
              <div className="p-2.5 rounded-lg bg-[#07111F] border border-[#20384D] space-y-1">
                <span className="text-[8px] font-mono font-bold text-[#FFB547] uppercase block">
                  Tactical Advantage
                </span>
                <p className="text-[9px] text-[#8FA8B8] leading-relaxed">
                  {routeData.comparison.reason}
                </p>
              </div>
            )}
          </SpotlightCard>
        )}

      </div>

      {/* Footer System Stamp */}
      <div className="pt-2 border-t border-[#20384D] text-[9px] text-[#8FA8B8] flex justify-between font-mono">
        <span>A* PostGIS Solver</span>
        <span>Aero-Hydro Validated</span>
      </div>
    </aside>
  );
}

export default RoutingSidebar;
