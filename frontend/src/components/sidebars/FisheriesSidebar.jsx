import React, { useState, useMemo } from 'react';
import { 
  Fish, 
  Layers, 
  Eye, 
  EyeOff, 
  MapPin, 
  Navigation, 
  Sparkles, 
  Thermometer, 
  Droplet, 
  Compass, 
  Waves,
  Wind,
  Activity,
  ChevronRight, 
  ShieldCheck, 
  Zap, 
  Info 
} from 'lucide-react';
import SpotlightCard from '../common/SpotlightCard';
import RiskBadge from '../common/RiskBadge';
import { MOCK_PFZ_LINES } from '../../services/mockData';

export function FisheriesSidebar({
  sstOpacity = 0.65,
  setSstOpacity,
  chlOpacity = 0.65,
  setChlOpacity,
  pfzList = MOCK_PFZ_LINES.features,
  selectedPfz = null,
  onSelectPfz,
  onDestinationSelect,
  selectedLocation = { lat: 18.96, lon: 72.82 },
  layersOverride = {},
  setLayersOverride,
  hoveredPfzId = null,
  onHoverPfz = () => {}
}) {
  const [sstVisible, setSstVisible] = useState(true);
  const [chlVisible, setChlVisible] = useState(true);

  const handleToggleSst = () => {
    if (sstVisible) {
      if (setSstOpacity) setSstOpacity(0);
      setSstVisible(false);
    } else {
      if (setSstOpacity) setSstOpacity(0.65);
      setSstVisible(true);
    }
  };

  const handleToggleChl = () => {
    if (chlVisible) {
      if (setChlOpacity) setChlOpacity(0);
      setChlVisible(false);
    } else {
      if (setChlOpacity) setChlOpacity(0.65);
      setChlVisible(true);
    }
  };

  const handleToggleWindHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      windVectors: !prev.windVectors,
      currentVectors: false
    }));
  };

  const handleToggleCurrentHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      currentVectors: !prev.currentVectors,
      windVectors: false
    }));
  };

  const handleToggleBsiHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      bsiRisk: !prev.bsiRisk,
      windSpeed: false,
      currentSpeed: false
    }));
  };

  const handleSetPfzDestination = (pfzFeature) => {
    if (!pfzFeature?.geometry?.coordinates?.length) return;
    let coords = pfzFeature.geometry.coordinates[0];
    
    // Handle MultiLineString where coordinates[0] is an array of points
    while (Array.isArray(coords[0])) {
        coords = coords[0];
    }
    
    if (onDestinationSelect) {
      onDestinationSelect({ lat: coords[1], lon: coords[0] });
    }
    if (onSelectPfz) {
      onSelectPfz(pfzFeature);
    }
  };

  const renderedPfzCards = useMemo(() => {
    return (pfzList || []).map((feat) => {
      const props = feat.properties || {};
      const isSelected = selectedPfz?.id === feat.id || selectedPfz?.properties?.id === feat.id;
      const featId = feat.id || props.id;
      const isHovered = hoveredPfzId === featId;
      const score = props.high_catch_score != null ? props.high_catch_score : (props.risk_score || 85);
      const offshoreName = props.offshore_name || `Zone ${featId || 'N/A'}`;

      const sstVal = props.sst_median != null ? `${Number(props.sst_median).toFixed(1)}°C` : 'N/A';
      const chlVal = props.chl_median != null ? `${Number(props.chl_median).toFixed(2)} mg/m³` : 'N/A';
      const currVal = props.current_median != null ? `${Number(props.current_median).toFixed(2)} m/s` : 'N/A';
      const waveVal = props.wave_hs_median != null ? `${Number(props.wave_hs_median).toFixed(2)} m` : 'N/A';

      return (
        <div
          key={featId}
          onClick={() => onSelectPfz && onSelectPfz(feat)}
          onMouseEnter={() => onHoverPfz(featId)}
          onMouseLeave={() => onHoverPfz(null)}
          className={`p-2.5 rounded-xl border transition-all cursor-pointer space-y-2 ${
            isSelected
              ? 'bg-[#FFB547]/15 border-[#FFB547] shadow-[0_0_12px_rgba(255,181,71,0.2)]'
              : isHovered
                ? 'bg-[#00D4FF]/10 border-[#00D4FF] shadow-[0_0_12px_rgba(0,212,255,0.2)]'
                : 'bg-[#07111F] border-[#20384D] hover:border-[#8FA8B8]/50'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="font-mono font-bold text-[11px] text-[#EAF4F8]">
              PFZ - Offshore {offshoreName}
            </span>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#18C7A0]/10 text-[#18C7A0] border border-[#18C7A0]/20">
              Score: {score}/100
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px] text-[#8FA8B8]">
            <div className="flex items-center gap-1.5">
              <Thermometer className="w-3 h-3 text-[#FF5C5C]" />
              <span>SST: <strong className="text-[#EAF4F8]">{sstVal}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Droplet className="w-3 h-3 text-[#18C7A0]" />
              <span>CHL: <strong className="text-[#EAF4F8]">{chlVal}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Compass className="w-3 h-3 text-[#00D4FF]" />
              <span>Current: <strong className="text-[#EAF4F8]">{currVal}</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <Waves className="w-3 h-3 text-[#FFB547]" />
              <span>Wave Hs: <strong className="text-[#EAF4F8]">{waveVal}</strong></span>
            </div>
          </div>

          <div className="pt-2 border-t border-[#20384D] flex items-center justify-between">
            <span className="text-[9px] text-[#8FA8B8]">Front Convergence</span>
            <span className="text-[9px] font-mono text-[#18C7A0]">Thermal-Plankton Optimal</span>
          </div>

          {isSelected && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleSetPfzDestination(feat);
              }}
              className="w-full mt-2 py-1.5 rounded bg-[#00D4FF]/10 hover:bg-[#00D4FF]/20 text-[#00D4FF] border border-[#00D4FF]/30 transition text-[10px] font-mono uppercase font-bold flex items-center justify-center gap-1.5"
            >
              <Navigation className="w-3 h-3" />
              <span>Set as Route Target</span>
            </button>
          )}
        </div>
      );
    });
  }, [pfzList, selectedPfz, onSelectPfz, onDestinationSelect]);

  return (
    <aside className="w-full h-full flex flex-col justify-between overflow-y-auto p-4 space-y-4 select-none font-sans text-xs">
      <div className="space-y-4">
        
        {/* 1. Header Banner */}
        <div className="flex items-center justify-between border-b border-[#20384D] pb-2.5">
          <div className="flex items-center gap-2">
            <Fish className="w-4 h-4 text-[#FFB547]" />
            <h2 className="font-mono font-bold text-sm text-[#EAF4F8] uppercase tracking-wider">
              Ocean Analytics
            </h2>
          </div>
          <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-[#FFB547]/10 text-[#FFB547] border border-[#FFB547]/30">
            MODE B
          </span>
        </div>

        {/* 2. Simulation Heatmap & Overlay Toggles Card */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#00D4FF]" />
              Simulation Heatmap Overlays
            </span>
            <span className="text-[9px] font-mono text-[#00D4FF] font-bold">LIVE GPU</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={handleToggleWindHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                (layersOverride || {}).windVectors
                  ? 'bg-[#00D4FF]/20 border-[#00D4FF] text-[#00D4FF] shadow-[0_0_10px_rgba(0,212,255,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">WIND VECTORS</span>
                <Wind className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {(layersOverride || {}).windVectors ? 'ACTIVE (km/h)' : 'OFF'}
              </span>
            </button>

            <button
              type="button"
              onClick={handleToggleCurrentHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                (layersOverride || {}).currentVectors
                  ? 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0] shadow-[0_0_10px_rgba(24,199,160,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">CURRENT VECTORS</span>
                <Compass className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {(layersOverride || {}).currentVectors ? 'ACTIVE (m/s)' : 'OFF'}
              </span>
            </button>
          </div>
        </SpotlightCard>

        {/* 3. INCOIS WMS Raster Heatmaps Opacity Card */}
        <SpotlightCard className="p-3.5 space-y-3.5">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#00D4FF]" />
              WMS Satellite Rasters
            </span>
            <span className="text-[9px] text-[#18C7A0] font-mono font-bold">DYNAMIC PROVENANCE</span>
          </div>

          {/* SST Opacity Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-[10px]">
              <div className="flex items-center gap-1.5 text-[#EAF4F8] font-medium">
                <Thermometer className="w-3.5 h-3.5 text-[#FF5C5C]" />
                <span>Sea Surface Temp (SST)</span>
              </div>
              <div className="flex items-center gap-2 font-mono">
                <span className="text-[#00D4FF] font-bold">{Math.round(sstOpacity * 100)}%</span>
                <button
                  type="button"
                  onClick={handleToggleSst}
                  className="text-[#8FA8B8] hover:text-[#EAF4F8] cursor-pointer"
                  title="Toggle SST Visibility"
                >
                  {sstVisible ? <Eye className="w-3 h-3 text-[#18C7A0]" /> : <EyeOff className="w-3 h-3 text-[#8FA8B8]" />}
                </button>
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={sstOpacity}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                if (setSstOpacity) setSstOpacity(val);
                setSstVisible(val > 0);
              }}
              className="w-full h-1.5 bg-[#07111F] rounded-lg appearance-none cursor-pointer accent-[#FF5C5C]"
            />
            <div className="flex justify-between text-[7.5px] font-mono text-[#8FA8B8]">
              <span>24°C (Cool)</span>
              <span className="text-[#18C7A0]">Optimal Front: 28°C - 30°C</span>
              <span>32°C (Warm)</span>
            </div>
          </div>

          {/* Chlorophyll-a Opacity Slider */}
          <div className="space-y-1.5 pt-2 border-t border-[#20384D]/60">
            <div className="flex justify-between items-center text-[10px]">
              <div className="flex items-center gap-1.5 text-[#EAF4F8] font-medium">
                <Droplet className="w-3.5 h-3.5 text-[#18C7A0]" />
                <span>Chlorophyll-a (CHL)</span>
              </div>
              <div className="flex items-center gap-2 font-mono">
                <span className="text-[#18C7A0] font-bold">{Math.round(chlOpacity * 100)}%</span>
                <button
                  type="button"
                  onClick={handleToggleChl}
                  className="text-[#8FA8B8] hover:text-[#EAF4F8] cursor-pointer"
                  title="Toggle CHL Visibility"
                >
                  {chlVisible ? <Eye className="w-3 h-3 text-[#18C7A0]" /> : <EyeOff className="w-3 h-3 text-[#8FA8B8]" />}
                </button>
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={chlOpacity}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                if (setChlOpacity) setChlOpacity(val);
                setChlVisible(val > 0);
              }}
              className="w-full h-1.5 bg-[#07111F] rounded-lg appearance-none cursor-pointer accent-[#18C7A0]"
            />
            <div className="flex justify-between text-[7.5px] font-mono text-[#8FA8B8]">
              <span>0.05 mg/m³</span>
              <span className="text-[#18C7A0]">High Plankton Gradient</span>
              <span>2.0 mg/m³</span>
            </div>
          </div>
        </SpotlightCard>

        {/* 4. Potential Fishing Zone (PFZ) Vector Lines Directory */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Fish className="w-3.5 h-3.5 text-[#FFB547]" />
              Active High Catch Vectors
            </span>
            <span className="text-[9px] font-mono text-[#FFB547] font-bold">
              {(pfzList || []).length} Zones
            </span>
          </div>

          <div className="space-y-2">
            {renderedPfzCards}
          </div>
        </SpotlightCard>

        {/* 5. Selected PFZ Detailed Zone Intelligence Card */}
        {selectedPfz && (
          <SpotlightCard className="p-3.5 space-y-2.5 border-[#FFB547]/40 bg-[#13263A]">
            <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
              <span className="text-[10px] font-mono font-bold text-[#FFB547] uppercase">
                Inspected PFZ Telemetry
              </span>
              <RiskBadge level="LOW" size="xs" />
            </div>

            <div className="text-[10px] text-[#8FA8B8] space-y-1 font-medium">
              <div className="flex justify-between">
                <span>Thermal Gradient Stability:</span>
                <span className="font-mono text-[#18C7A0] font-bold">OPTIMAL</span>
              </div>
              <div className="flex justify-between">
                <span>Plankton Convergence:</span>
                <span className="font-mono text-[#EAF4F8] font-bold">Front Identified</span>
              </div>
              <div className="flex justify-between">
                <span>Median Wave Height (Hs):</span>
                <span className="font-mono text-[#EAF4F8] font-bold">
                  {selectedPfz.properties?.wave_hs_median != null ? `${Number(selectedPfz.properties.wave_hs_median).toFixed(2)} m` : '1.20 m'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Median Surface Current:</span>
                <span className="font-mono text-[#00D4FF] font-bold">
                  {selectedPfz.properties?.current_median != null ? `${Number(selectedPfz.properties.current_median).toFixed(2)} m/s` : '0.35 m/s'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Advisory Validity Epoch:</span>
                <span className="font-mono text-[#8FA8B8]">
                  {selectedPfz.properties?.validity || new Date().toLocaleDateString('en-GB', {day: '2-digit', month: 'short', year: 'numeric'})}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleSetPfzDestination(selectedPfz)}
              className="w-full py-2 rounded-lg bg-[#FFB547] hover:bg-[#FFC470] text-[#07111F] font-mono font-bold text-xs uppercase tracking-wider transition flex items-center justify-center gap-1.5 cursor-pointer shadow-md"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>Route Vessel to Zone</span>
            </button>
          </SpotlightCard>
        )}

      </div>

      {/* Footer System Stamp */}
      <div className="pt-2 border-t border-[#20384D] text-[9px] text-[#8FA8B8] flex justify-between font-mono">
        <span>INCOIS PFZ Advisories</span>
        <span>MODIS / OCM-3 Feeds</span>
      </div>
    </aside>
  );
}

export default FisheriesSidebar;

