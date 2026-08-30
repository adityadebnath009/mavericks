import React from 'react';
import { 
  Wind, 
  Waves, 
  Calendar, 
  Clock, 
  AlertTriangle, 
  ShieldCheck, 
  Compass, 
  Info, 
  Layers, 
  Thermometer, 
  Radio, 
  FileText,
  Activity
} from 'lucide-react';
import SpotlightCard from '../common/SpotlightCard';
import RiskBadge from '../common/RiskBadge';

export function WeatherSidebar({
  selectedDay = 1,
  setSelectedDay,
  selectedHour = 12,
  setSelectedHour,
  safetyData = null,
  layersOverride = {},
  setLayersOverride
}) {
  const hoursList = [0, 3, 6, 9, 12, 15, 18, 21];

  const overallRisk = safetyData?.navik_risk?.overall_status || safetyData?.rating || 'LOW';
  const raw = safetyData?.raw_metrics || {};
  const dailyBsi = safetyData?.provenance?.daily_bsi_forecast || {
    day1: { score: 1, rating: 'SAFE' },
    day2: { score: 1, rating: 'SAFE' },
    day3: { score: 2, rating: 'SAFE' }
  };

  // Dynamically calculate UTC dates for the 3-day forecast
  const getUtcDateString = (dayOffset) => {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() + (dayOffset - 1));
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };
  const getUtcLabel = (dayOffset) => {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() + (dayOffset - 1));
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }).toUpperCase();
  };

  const selectedDateStr = getUtcDateString(selectedDay);
  const selectedTimeStr = `${String(selectedHour).padStart(2, '0')}:00 UTC`;

  const handleToggleWindHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      windSpeed: !prev.windSpeed,
      currentSpeed: false
    }));
  };

  const handleToggleCurrentHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      currentSpeed: !prev.currentSpeed,
      windSpeed: false
    }));
  };

  const handleToggleBsiHeatmap = () => {
    if (!setLayersOverride) return;
    setLayersOverride(prev => ({
      ...prev,
      bsiRisk: !prev.bsiRisk
    }));
  };

  return (
    <aside className="w-full h-full flex flex-col justify-between overflow-y-auto p-4 space-y-4 select-none font-sans text-xs">
      <div className="space-y-4">
        
        {/* 1. Header Banner */}
        <div className="flex items-center justify-between border-b border-[#20384D] pb-2.5">
          <div className="flex items-center gap-2">
            <Wind className="w-4 h-4 text-[#00D4FF]" />
            <h2 className="font-mono font-bold text-sm text-[#EAF4F8] uppercase tracking-wider">
              Meteorological Hazards
            </h2>
          </div>
          <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30">
            MODE C
          </span>
        </div>

        {/* 2. Simulation Heatmap & Overlay Toggles Card */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#00D4FF]" />
              Simulation Heatmap Overlays
            </span>
            <span className="text-[9px] font-mono text-[#00D4FF] font-bold">GPU SHADER</span>
          </div>

                    <div className="grid grid-cols-3 gap-2">
            {/* Wind Vector Toggle */}
            <button
              type="button"
              onClick={handleToggleWindHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.windSpeed
                  ? 'bg-[#00D4FF]/20 border-[#00D4FF] text-[#00D4FF] shadow-[0_0_10px_rgba(0,212,255,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">WIND VECTORS</span>
                <Wind className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.windSpeed ? 'ACTIVE' : 'OFF'}
              </span>
            </button>

            {/* Surface CURRENT VECTORS Toggle */}
            <button
              type="button"
              onClick={handleToggleCurrentHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.currentSpeed
                  ? 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0] shadow-[0_0_10px_rgba(24,199,160,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">CURRENTS</span>
                <Compass className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.currentSpeed ? 'ACTIVE' : 'OFF'}
              </span>
            </button>
            
            {/* BSI Heatmap Toggle */}
            <button
              type="button"
              onClick={handleToggleBsiHeatmap}
              className={`p-2 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                layersOverride.bsiRisk
                  ? 'bg-[#FF5C5C]/20 border-[#FF5C5C] text-[#FF5C5C] shadow-[0_0_10px_rgba(255,92,92,0.25)]'
                  : 'bg-[#07111F] border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]/50'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="text-[8px] font-mono uppercase font-bold">BSI HEATMAP</span>
                <AlertTriangle className="w-3.5 h-3.5" />
              </div>
              <span className="text-[9px] font-mono font-bold mt-1">
                {layersOverride.bsiRisk ? 'ACTIVE' : 'OFF'}
              </span>
            </button>
          </div>

        </SpotlightCard>

        {/* 3. 3-Day Forecast Epoch Cards */}
        <SpotlightCard className="p-3.5 space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#00D4FF]" />
              3-Day SVAS Forecast Horizon
            </span>
            <span className="text-[9px] font-mono text-[#8FA8B8]">0.4° Grid</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[1, 2, 3].map((d) => {
              const dayKey = `day${d}`;
              const data = dailyBsi[dayKey] || { score: 1, rating: 'SAFE' };
              const dateLabel = getUtcLabel(d);
              const isSelected = selectedDay === d;

              return (
                <button
                  key={d}
                  type="button"
                  onClick={() => setSelectedDay && setSelectedDay(d)}
                  className={`p-2.5 rounded-xl border text-center transition cursor-pointer flex flex-col items-center justify-between ${
                    isSelected
                      ? 'bg-[#00D4FF]/15 border-[#00D4FF] shadow-[0_0_12px_rgba(0,212,255,0.25)]'
                      : 'bg-[#07111F] border-[#20384D] hover:border-[#8FA8B8]/50'
                  }`}
                >
                  <span className="text-[8px] font-mono font-bold text-[#8FA8B8] block">{dateLabel}</span>
                  <span className="text-sm font-black font-mono text-[#EAF4F8] my-0.5 block">
                    {data.score}/7
                  </span>
                  <RiskBadge level={data.rating} size="xs" showIcon={false} />
                </button>
              );
            })}
          </div>
        </SpotlightCard>

        {/* 3. 24-Hour Diurnal Time Scrubber Card */}
        <SpotlightCard className="p-3.5 space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#00D4FF]" />
              Diurnal Time Step (UTC)
            </span>
            <span className="text-[9px] font-mono font-bold text-[#00D4FF]">
              {selectedTimeStr}
            </span>
          </div>

          {/* Scrubber Buttons Grid */}
          <div className="grid grid-cols-4 gap-1.5">
            {hoursList.map((h) => {
              const isSelected = selectedHour === h;
              return (
                <button
                  key={h}
                  type="button"
                  onClick={() => setSelectedHour && setSelectedHour(h)}
                  className={`py-1 rounded font-mono text-[9px] font-bold transition cursor-pointer text-center ${
                    isSelected
                      ? 'bg-[#00D4FF] text-[#07111F] shadow'
                      : 'bg-[#07111F] border border-[#20384D] text-[#8FA8B8] hover:text-[#EAF4F8]'
                  }`}
                >
                  {String(h).padStart(2, '0')}:00
                </button>
              );
            })}
          </div>

          <input
            type="range"
            min="0"
            max="7"
            value={hoursList.indexOf(selectedHour)}
            onChange={(e) => setSelectedHour && setSelectedHour(hoursList[parseInt(e.target.value)])}
            className="w-full h-1.5 bg-[#07111F] rounded-lg appearance-none cursor-pointer accent-[#00D4FF]"
          />
        </SpotlightCard>

        {/* 4. Ocean State Telemetry Gauges Card */}
        <SpotlightCard className="p-3.5 space-y-3">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#8FA8B8] uppercase flex items-center gap-1.5">
              <Waves className="w-3.5 h-3.5 text-[#00D4FF]" />
              Ocean State Telemetry
            </span>
            <RiskBadge level={overallRisk} size="xs" />
          </div>

          <div className="grid grid-cols-2 gap-2 text-[9px]">
            <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
              <span className="text-[8px] text-[#8FA8B8] block">Significant Wave (Hs)</span>
              <span className="text-xs font-mono font-bold text-[#EAF4F8] mt-0.5 block">
                {raw.inspect_hs != null ? `${Number(raw.inspect_hs).toFixed(2)} m` : '1.20 m'}
              </span>
              <span className="text-[7.5px] text-[#18C7A0] font-mono">Safe (&lt; 2.5m)</span>
            </div>

            <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
              <span className="text-[8px] text-[#8FA8B8] block">Wave Steepness (STP)</span>
              <span className="text-xs font-mono font-bold text-[#EAF4F8] mt-0.5 block">
                {raw.inspect_stp ?? '0.012'}
              </span>
              <span className="text-[7.5px] text-[#18C7A0] font-mono">Non-Breaking</span>
            </div>

            <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
              <span className="text-[8px] text-[#8FA8B8] block">Wind Sea Height (Hsea)</span>
              <span className="text-xs font-mono font-bold text-[#EAF4F8] mt-0.5 block">
                {raw.inspect_hsea != null ? `${Number(raw.inspect_hsea).toFixed(2)} m` : '0.80 m'}
              </span>
              <span className="text-[7.5px] text-[#8FA8B8] font-mono">Period: {raw.inspect_t02 ?? 6.5}s</span>
            </div>

            <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
              <span className="text-[8px] text-[#8FA8B8] block">Mean Wave Dir (MWD)</span>
              <span className="text-xs font-mono font-bold text-[#EAF4F8] mt-0.5 block">
                {raw.inspect_mwd ?? 210}° SW
              </span>
              <span className="text-[7.5px] text-[#8FA8B8] font-mono">Spread: {raw.inspect_spr ?? 0.24}</span>
            </div>

            <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
              <span className="text-[8px] text-[#8FA8B8] block">Wind Speed (Peak)</span>
              <span className="text-xs font-mono font-bold text-[#FFB547] mt-0.5 block">
                {raw.inspect_wind != null ? `${Number(raw.inspect_wind).toFixed(1)} km/h` : '18.5 km/h'}
              </span>
              <span className="text-[7.5px] text-[#8FA8B8] font-mono">Peak: {raw.wind_speed_kmh ?? 18.5} km/h</span>
            </div>

            <div className="bg-[#07111F] p-2 rounded-lg border border-[#20384D]">
              <span className="text-[8px] text-[#8FA8B8] block">Surface Current</span>
              <span className="text-xs font-mono font-bold text-[#18C7A0] mt-0.5 block">
                {raw.inspect_curr != null ? `${Number(raw.inspect_curr).toFixed(2)} m/s` : '0.35 m/s'}
              </span>
              <span className="text-[7.5px] text-[#8FA8B8] font-mono">112° ESE</span>
            </div>
          </div>
        </SpotlightCard>

        {/* 5. INCOIS District Advisory Viewer */}
        <SpotlightCard className="p-3.5 space-y-2 border-[#18C7A0]/40">
          <div className="flex items-center justify-between border-b border-[#20384D] pb-1.5">
            <span className="text-[10px] font-mono font-bold text-[#18C7A0] uppercase flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[#18C7A0]" />
              Official INCOIS Advisory
            </span>
            <span className="text-[9px] font-mono text-[#8FA8B8]">SVAS Clause</span>
          </div>

          <p className="text-[10px] text-[#EAF4F8] leading-relaxed">
            {safetyData?.recommendation || 'Safe to venture into sea. All wave-forcing indicators are within standard operating limits.'}
          </p>

          <div className="pt-1 text-[8px] font-mono text-[#8FA8B8] flex justify-between">
            <span>Source: INCOIS Hyderabad</span>
            <span>Epoch: {selectedDateStr}</span>
          </div>
        </SpotlightCard>

      </div>

      {/* Footer System Stamp */}
      <div className="pt-2 border-t border-[#20384D] text-[9px] text-[#8FA8B8] flex justify-between font-mono">
        <span>WW3 Wavewatch-III</span>
        <span>NIO Ocean Currents</span>
      </div>
    </aside>
  );
}

export default WeatherSidebar;
