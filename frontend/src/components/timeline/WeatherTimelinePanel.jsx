import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  AreaChart, 
  Area, 
  Cell 
} from 'recharts';
import { ChevronDown, ChevronUp, Clock, Activity } from 'lucide-react';
import SpotlightCard from '../common/SpotlightCard';

export function WeatherTimelinePanel({
  forecastTimeline = [],
  selectedHour = 12,
  onSelectHour,
  selectedDay = 1,
  className = ''
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const getBarColor = (score) => {
    if (score >= 6) return '#FF5C5C';
    if (score >= 4) return '#FFB547';
    if (score >= 2) return '#FFB547';
    return '#18C7A0';
  };

  const getUtcDateString = (dayOffset) => {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() + (dayOffset - 1));
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
  };
  const selectedDateStr = getUtcDateString(selectedDay);

  return (
    <section 
      className={`bg-[#0D1B2A] border-t border-[#20384D] select-none transition-all duration-300 z-20 shrink-0 ${className} ${
        isCollapsed ? 'h-9' : 'h-48 min-h-[192px]'
      }`}
      aria-label="24-Hour Diurnal Weather Timeline"
    >
      {/* Top Header Bar */}
      <div className="h-9 px-4 sm:px-6 flex items-center justify-between border-b border-[#20384D] bg-[#07111F]/60 text-xs">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-[#00D4FF]" />
          <span className="font-mono font-bold text-[#EAF4F8] text-[11px] uppercase tracking-wider">
            24-Hour Diurnal Forecast Trends // {selectedDateStr}
          </span>
          <span className="hidden sm:inline text-[9px] font-mono text-[#8FA8B8]">
            (Synchronized INCOIS WW3 & NIO Feeds)
          </span>
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center gap-1 text-[10px] font-mono text-[#8FA8B8] hover:text-[#EAF4F8] px-2 py-0.5 rounded bg-[#13263A] border border-[#20384D] transition cursor-pointer"
        >
          <span>{isCollapsed ? 'EXPAND TIMELINE' : 'COLLAPSE'}</span>
          {isCollapsed ? <ChevronUp className="w-3 h-3 text-[#00D4FF]" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* 4 Synchronized Charts Grid */}
      {!isCollapsed && (
        <div className="p-3 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 h-[calc(100%-36px)] overflow-hidden">
          
          {/* Chart 1: SVAS BSI Risk Score BarChart */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-xl p-2.5 flex flex-col justify-between overflow-hidden shadow-md">
            <div className="flex justify-between items-center text-[9px] font-mono">
              <span className="text-[#8FA8B8] font-bold uppercase">SVAS BSI Capsizing Score</span>
              <span className="text-[#18C7A0] font-bold">0 — 7 Index</span>
            </div>
            <div className="w-full h-24 mt-1">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -20, bottom: 2 }}>
                  <XAxis dataKey="time" tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 7]} tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#07111F', borderColor: '#20384D', borderRadius: '8px', fontSize: '10px' }} 
                    labelStyle={{ color: '#8FA8B8', fontWeight: 'bold' }}
                    itemStyle={{ color: '#EAF4F8' }}
                    formatter={(value) => [`${value} / 7`, 'BSI Score']}
                  />
                  <Bar dataKey="bsi" radius={[3, 3, 0, 0]}>
                    {forecastTimeline.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getBarColor(entry.bsi)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Significant Wave Height (Hs) AreaChart */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-xl p-2.5 flex flex-col justify-between overflow-hidden shadow-md">
            <div className="flex justify-between items-center text-[9px] font-mono">
              <span className="text-[#8FA8B8] font-bold uppercase">Wave Height (Hs)</span>
              <span className="text-[#00D4FF] font-bold">Meters (m)</span>
            </div>
            <div className="w-full h-24 mt-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -20, bottom: 2 }}>
                  <defs>
                    <linearGradient id="waveFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#00D4FF" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#07111F', borderColor: '#20384D', borderRadius: '8px', fontSize: '10px' }} 
                    labelStyle={{ color: '#8FA8B8', fontWeight: 'bold' }}
                    itemStyle={{ color: '#00D4FF' }}
                    formatter={(value) => [`${value} m`, 'Wave Height']}
                  />
                  <Area type="monotone" dataKey="wave_height" stroke="#00D4FF" strokeWidth={2} fill="url(#waveFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: Peak Wind Speed AreaChart */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-xl p-2.5 flex flex-col justify-between overflow-hidden shadow-md">
            <div className="flex justify-between items-center text-[9px] font-mono">
              <span className="text-[#8FA8B8] font-bold uppercase">Wind Speed (Peak)</span>
              <span className="text-[#FFB547] font-bold">km / h</span>
            </div>
            <div className="w-full h-24 mt-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -20, bottom: 2 }}>
                  <defs>
                    <linearGradient id="windFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FFB547" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#FFB547" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#07111F', borderColor: '#20384D', borderRadius: '8px', fontSize: '10px' }} 
                    labelStyle={{ color: '#8FA8B8', fontWeight: 'bold' }}
                    itemStyle={{ color: '#FFB547' }}
                    formatter={(value) => [`${value} km/h`, 'Wind Speed']}
                  />
                  <Area type="monotone" dataKey="wind_speed" stroke="#FFB547" strokeWidth={2} fill="url(#windFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 4: Surface Current Speed AreaChart */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-xl p-2.5 flex flex-col justify-between overflow-hidden shadow-md">
            <div className="flex justify-between items-center text-[9px] font-mono">
              <span className="text-[#8FA8B8] font-bold uppercase">Surface Current Velocity</span>
              <span className="text-[#18C7A0] font-bold">m / s</span>
            </div>
            <div className="w-full h-24 mt-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -20, bottom: 2 }}>
                  <defs>
                    <linearGradient id="currFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#18C7A0" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#18C7A0" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8FA8B8', fontSize: 8 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#07111F', borderColor: '#20384D', borderRadius: '8px', fontSize: '10px' }} 
                    labelStyle={{ color: '#8FA8B8', fontWeight: 'bold' }}
                    itemStyle={{ color: '#18C7A0' }}
                    formatter={(value) => [`${value} m/s`, 'Current Velocity']}
                  />
                  <Area type="monotone" dataKey="current_speed" stroke="#18C7A0" strokeWidth={2} fill="url(#currFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      )}
    </section>
  );
}

export default WeatherTimelinePanel;
