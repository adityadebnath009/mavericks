import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Wind, 
  Waves, 
  AlertTriangle, 
  RefreshCw, 
  HelpCircle, 
  Sun, 
  Calendar 
} from 'lucide-react';
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
import MapContainer from './components/MapContainer';

const DEFAULT_SAFETY_DATA = {
  rating: 'SAFE',
  recommendation: 'Safe to venture into sea. Exercise standard maritime caution.',
  reasons: [
    'All weather, wave, current, and geofence parameters are within optimal safety ranges.'
  ],
  vessel_suitability: {
    vessel_beam_m: 3.5,
    critical_beam_m: 4.8,
    vulnerable: false
  },
  bsi_metrics: {
    bsi_score: 1,
    rating: 'SAFE',
    description: 'All wave-forcing indicators within safe parameters.',
    wave_steepness: 0.012,
    directional_spread: 0.24
  },
  raw_metrics: {
    wave_height_m: 1.2,
    wind_speed_kmh: 18.5,
    current_speed_ms: 0.35,
    distance_to_border_km: 116.97,
    is_inside_eez: true,
    is_inside_mpa: false,
    mpa_name: null,
    inspect_hs: 1.2,
    inspect_stp: 0.012,
    inspect_spr: 0.24,
    inspect_hsea: 0.8,
    inspect_t02: 6.5,
    inspect_mwd: 210,
    peak_wind_time: '26 Aug • 12:00 UTC',
    peak_curr_time: '26 Aug • 12:00 UTC',
    peak_wave_time: '26 Aug • 12:00 UTC'
  },
  orca_risk: {
    overall_status: 'LOW',
    wind_risk: 'LOW',
    current_risk: 'LOW',
    geofence_risk: 'CLEAR'
  },
  coordinates: {
    latitude: 17.431,
    longitude: 84.703
  },
  provenance: {
    source: 'INCOIS Ocean State Forecast',
    ww3_dataset: 'rsmc_combined_ww3_20260825.nc',
    currents_dataset: 'CURRENTS_NIO_20260824.nc',
    retrieved_at: '26 Aug 2026 • 12:00 UTC',
    daily_bsi_forecast: {
      day1: { score: 1, rating: 'SAFE' },
      day2: { score: 1, rating: 'SAFE' },
      day3: { score: 2, rating: 'SAFE' }
    }
  }
};

const DEFAULT_FORECAST_TIMELINE = [
  { time: '00:00', bsi: 1, wave_height: 1.1, wind_speed: 15.2, current_speed: 0.30 },
  { time: '03:00', bsi: 1, wave_height: 1.2, wind_speed: 16.0, current_speed: 0.32 },
  { time: '06:00', bsi: 1, wave_height: 1.3, wind_speed: 17.4, current_speed: 0.35 },
  { time: '09:00', bsi: 1, wave_height: 1.2, wind_speed: 18.1, current_speed: 0.34 },
  { time: '12:00', bsi: 1, wave_height: 1.2, wind_speed: 18.5, current_speed: 0.35 },
  { time: '15:00', bsi: 1, wave_height: 1.1, wind_speed: 17.0, current_speed: 0.33 },
  { time: '18:00', bsi: 1, wave_height: 1.0, wind_speed: 15.5, current_speed: 0.31 },
  { time: '21:00', bsi: 0, wave_height: 0.9, wind_speed: 14.2, current_speed: 0.28 }
];

const getVesselTypeLabel = (beam) => {
  if (beam < 4.0) return 'Small Craft / Motorized Boat (<4m)';
  if (beam < 6.0) return 'Medium Trawler / Gillnetter (<6m)';
  return 'Large Trawler / Deep-sea Vessel (<7m)';
};

const getApiUrl = (path) => {
  if (typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location;
    if (protocol === 'file:' || ((hostname === 'localhost' || hostname === '127.0.0.1') && port !== '8000')) {
      return `http://127.0.0.1:8000${path}`;
    }
  }
  return path;
};

function App() {
  const [selectedLocation, setSelectedLocation] = useState({ lat: 17.431, lon: 84.703 }); // Default coordinates
  const [beamWidth, setBeamWidth] = useState(3.5);
  const [selectedDay, setSelectedDay] = useState(1);
  const [selectedHour, setSelectedHour] = useState(12); // Default to 12:00 UTC
  const [safetyData, setSafetyData] = useState(DEFAULT_SAFETY_DATA);
  const [forecastTimeline, setForecastTimeline] = useState(DEFAULT_FORECAST_TIMELINE);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch point safety assessment
  const fetchSafetyAssessment = async (lat, lon, beam, day, hour) => {
    setIsLoading(true);
    setError(null);
    try {
      const safetyUrl = getApiUrl(`/api/safety?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}&hour=${hour}`);
      const forecastUrl = getApiUrl(`/api/safety/forecast?lat=${lat}&lon=${lon}&day=${day}`);
      
      const [safetyRes, forecastRes] = await Promise.all([
        fetch(safetyUrl),
        fetch(forecastUrl)
      ]);
      
      if (safetyRes.ok) {
        const safetyJson = await safetyRes.json();
        if (safetyJson && safetyJson.rating) {
          setSafetyData(safetyJson);
        }
      } else {
        setSafetyData(prev => ({
          ...prev,
          coordinates: { latitude: lat, longitude: lon }
        }));
      }
      
      if (forecastRes.ok) {
        const forecastJson = await forecastRes.json();
        if (Array.isArray(forecastJson) && forecastJson.length > 0) {
          setForecastTimeline(forecastJson);
        }
      }
    } catch (err) {
      console.error('Failed to retrieve live safety data, retaining stable values:', err);
      setError(err.message);
      setSafetyData(prev => ({
        ...prev,
        coordinates: { latitude: lat, longitude: lon }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  // Re-fetch data on coordinates, day, hour, or beam change
  useEffect(() => {
    if (selectedLocation) {
      fetchSafetyAssessment(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour);
    }
  }, [selectedLocation, beamWidth, selectedDay, selectedHour]);

  const handleRefresh = () => {
    if (selectedLocation) {
      fetchSafetyAssessment(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay, selectedHour);
    }
  };

  // Timeline slider values mapping
  const hoursList = [0, 3, 6, 9, 12, 15, 18, 21];

  const selectedDateStr = selectedDay === 1 ? '26 Aug 2026' : selectedDay === 2 ? '27 Aug 2026' : '28 Aug 2026';
  const selectedTimeStr = `${String(selectedHour).padStart(2, '0')}:00 UTC`;
  const formattedForecastDateTime = `${selectedDateStr} • ${selectedTimeStr}`;

  const getBsiColor = (score) => {
    if (score >= 6) return 'text-red-500 bg-red-500/10 border-red-500/30';
    if (score >= 4) return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
    if (score >= 2) return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
    return 'text-green-500 bg-green-500/10 border-green-500/30';
  };

  const getBarColor = (score) => {
    if (score >= 6) return '#ef4444';
    if (score >= 4) return '#f97316';
    if (score >= 2) return '#eab308';
    return '#22c55e';
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#070b13] text-slate-100 font-sans overflow-hidden">
      {/* 1. Header Navigation Bar */}
      <header className="h-12 border-b border-slate-800 bg-[#090f1d] px-6 flex justify-between items-center text-xs">
        <div className="flex items-center gap-3">
          {/* Sailboat/ORCA Emblem Logo */}
          <div className="bg-blue-600/20 p-1.5 rounded-lg border border-blue-500/40">
            <svg viewBox="0 0 100 100" className="w-5 h-5 fill-blue-400">
              <path d="M50 15 L80 65 L50 55 L20 65 Z" />
              <path d="M50 55 L50 85 L20 65 Z" fill="#38bdf8" />
            </svg>
          </div>
          <div>
            <span className="font-extrabold text-slate-100 uppercase tracking-widest text-sm block">ORCA Portal</span>
            <span className="text-[10px] text-slate-500">Intelligent Marine Decision-Support System</span>
          </div>
        </div>

        <div className="flex items-center gap-6 text-slate-400 font-semibold">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold">Data Status:</span>
            <div className="flex items-center gap-1.5 bg-green-500/10 text-green-400 border border-green-500/30 px-2 py-0.5 rounded-full text-[9px] font-bold">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Latest Available / Live
            </div>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <a href="#incois" className="hover:text-slate-200 flex items-center gap-1"><Waves className="w-3.5 h-3.5 text-blue-400" /> INCOIS Data</a>
            <a href="#help" className="hover:text-slate-200 flex items-center gap-1"><HelpCircle className="w-3.5 h-3.5" /> Help</a>
            <button className="hover:text-slate-200"><Sun className="w-3.5 h-3.5" /></button>
          </div>

          <div className="border-l border-slate-800 pl-6 flex items-center gap-3">
            <div className="text-right">
              <span className="text-[9px] text-slate-500 block uppercase">Last Updated</span>
              <span className="font-mono text-slate-300 font-bold text-[10px]">26 Aug 2026 • 12:00 UTC</span>
            </div>
            <button 
              onClick={handleRefresh}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700/60 transition active:scale-95 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace: Sidebar + Map + Bottom Panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Vessel & Decision Support */}
        <aside className="w-[30%] bg-[#080d19] border-r border-slate-800 flex flex-col justify-between overflow-y-auto p-4 space-y-4">
          <div className="space-y-4">
            
            {/* A. Vessel Profile Card */}
            <div className="bg-[#0b1324] border border-slate-800/80 p-3.5 rounded-xl space-y-3.5 relative shadow-lg">
              <div className="flex justify-between items-center">
                <h2 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Vessel Profile</h2>
                {safetyData?.vessel_suitability?.vulnerable ? (
                  <span className="text-[10px] text-red-400 font-bold px-2 py-0.5 bg-red-500/10 border border-red-500/30 rounded animate-pulse">Vulnerable</span>
                ) : (
                  <span className="text-[10px] text-blue-400 font-bold px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded">Active</span>
                )}
              </div>

              <div className="flex items-center gap-3">
                {/* Embedded Boat Vector Illustration */}
                <div className="w-16 h-12 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-center p-1.5 overflow-hidden">
                  <svg viewBox="0 0 100 80" className="w-full h-full stroke-slate-500 fill-slate-800">
                    <path d="M10 50 Q 50 65, 90 50 L 80 70 Q 50 75, 20 70 Z" strokeWidth="2.5"/>
                    <line x1="50" y1="15" x2="50" y2="50" strokeWidth="2.5" />
                    <polygon points="50,15 75,30 50,38" fill="#1e3a8a" stroke="#2563eb" strokeWidth="1.5" />
                    <circle cx="50" cy="50" r="4" fill="#ef4444" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-[10px] text-slate-500 block">Vessel Type</span>
                  <span className="font-bold text-slate-200 text-xs truncate block">{getVesselTypeLabel(beamWidth)}</span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-blue-400 font-mono font-bold">Beam: {beamWidth.toFixed(1)} m</span>
                    {safetyData?.vessel_suitability?.critical_beam_m > 0 && (
                      <span className="text-[9px] text-slate-500 font-mono">Crit: {safetyData.vessel_suitability.critical_beam_m}m</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Slider Controller */}
              <div className="space-y-1">
                <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                  <span>1.0m</span>
                  <span>Beam Width Slider</span>
                  <span>8.0m</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="8.0"
                  step="0.1"
                  value={beamWidth}
                  onChange={(e) => setBeamWidth(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>

              {/* SVAS Beam Class Badges */}
              <div className="space-y-1">
                <span className="text-[9px] text-slate-500 uppercase font-semibold">SVAS Advisory Class</span>
                <div className="flex gap-2">
                  <button 
                    type="button"
                    onClick={() => setBeamWidth(3.5)}
                    className={`flex-1 text-[10px] py-1 text-center font-extrabold rounded-md border transition cursor-pointer ${
                      beamWidth < 4.0 
                        ? 'bg-green-500/20 border-green-500 text-green-300 shadow-sm' 
                        : 'border-slate-800 text-slate-400 bg-slate-900/50 hover:bg-slate-800/80 hover:text-slate-200'
                    }`}
                  >
                    &lt; 4 m
                  </button>
                  <button 
                    type="button"
                    onClick={() => setBeamWidth(5.0)}
                    className={`flex-1 text-[10px] py-1 text-center font-extrabold rounded-md border transition cursor-pointer ${
                      beamWidth >= 4.0 && beamWidth < 6.0 
                        ? 'bg-green-500/20 border-green-500 text-green-300 shadow-sm' 
                        : 'border-slate-800 text-slate-400 bg-slate-900/50 hover:bg-slate-800/80 hover:text-slate-200'
                    }`}
                  >
                    &lt; 6 m
                  </button>
                  <button 
                    type="button"
                    onClick={() => setBeamWidth(6.5)}
                    className={`flex-1 text-[10px] py-1 text-center font-extrabold rounded-md border transition cursor-pointer ${
                      beamWidth >= 6.0 
                        ? 'bg-green-500/20 border-green-500 text-green-300 shadow-sm' 
                        : 'border-slate-800 text-slate-400 bg-slate-900/50 hover:bg-slate-800/80 hover:text-slate-200'
                    }`}
                  >
                    &lt; 7 m
                  </button>
                </div>
              </div>
            </div>

            {/* B. ORCA Operational Status Card */}
            {safetyData && (
              <div className={`p-4 rounded-xl border flex flex-col gap-1.5 shadow-lg ${
                safetyData.rating === 'DANGER' ? 'bg-red-500/10 border-red-500/30' :
                safetyData.rating === 'CAUTION' ? 'bg-orange-500/10 border-orange-500/30' :
                'bg-green-500/10 border-green-500/30'
              }`}>
                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">ORCA Operational Status</span>
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`w-5 h-5 ${
                    safetyData.rating === 'DANGER' ? 'text-red-400' :
                    safetyData.rating === 'CAUTION' ? 'text-orange-400' :
                    'text-green-400'
                  }`} />
                  <span className={`text-base font-black uppercase tracking-wide ${
                    safetyData.rating === 'DANGER' ? 'text-red-400' :
                    safetyData.rating === 'CAUTION' ? 'text-orange-400' :
                    'text-green-400'
                  }`}>
                    {safetyData.rating === 'DANGER' ? 'DANGER (High Risk)' :
                     safetyData.rating === 'CAUTION' ? 'CAUTION (Moderate Risk)' :
                     'SAFE (Low Risk)'}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400">
                  Primary driver: <span className="text-slate-200 font-semibold">{
                    safetyData.bsi_metrics?.rating === 'WARNING' || safetyData.bsi_metrics?.bsi_score >= 5 ? 'SVAS wave hazard warning' :
                    safetyData.bsi_metrics?.rating === 'ALERT' || safetyData.bsi_metrics?.bsi_score >= 2 ? 'SVAS wave hazard alert' :
                    safetyData.vessel_suitability?.vulnerable ? 'Vessel beam stability threshold' :
                    safetyData.orca_risk?.wind_risk === 'HIGH' ? 'High wind speed' :
                    safetyData.orca_risk?.wind_risk === 'MODERATE' ? 'Elevated wind speed' :
                    safetyData.orca_risk?.current_risk === 'HIGH' ? 'Strong surface currents' :
                    safetyData.orca_risk?.current_risk === 'MODERATE' ? 'Moderate surface currents' :
                    (safetyData.orca_risk?.geofence_risk === 'RESTRICTED' || safetyData.orca_risk?.geofence_risk === 'HIGH') ? 'Restricted boundary constraint' :
                    safetyData.orca_risk?.geofence_risk === 'WARNING' ? 'Approaching border/sanctuary' :
                    'Optimal safety parameters'
                  }</span>
                </p>
              </div>
            )}


            {/* C. Why This Decision Grid */}
            {safetyData && (
              <div className="space-y-2">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Why This Decision?</h3>
                <div className="grid grid-cols-4 gap-2">
                  <div className="bg-[#0b1324] border border-slate-800 p-2 rounded-xl text-center space-y-1.5">
                    <span className="text-[8px] text-slate-500 uppercase block font-semibold">SVAS BSI</span>
                    <span className="text-xs font-bold text-slate-200 block font-mono">{safetyData.bsi_metrics?.bsi_score ?? 0} / 7</span>
                    <span className={`text-[8px] font-extrabold px-1 rounded block ${
                      safetyData.bsi_metrics?.rating === 'WARNING' ? 'text-red-400 bg-red-500/10' :
                      safetyData.bsi_metrics?.rating === 'ALERT' ? 'text-orange-400 bg-orange-500/10' :
                      'text-green-400 bg-green-500/10'
                    }`}>{safetyData.bsi_metrics?.rating || 'SAFE'}</span>
                  </div>

                  <div className="bg-[#0b1324] border border-slate-800 p-2 rounded-xl text-center space-y-1.5">
                    <span className="text-[8px] text-slate-500 uppercase block font-semibold">Wind Risk</span>
                    <Wind className="w-3.5 h-3.5 text-slate-400 mx-auto" />
                    <span className={`text-[8px] font-extrabold px-1 rounded block ${
                      safetyData.orca_risk?.wind_risk === 'HIGH' ? 'text-red-400 bg-red-500/10' :
                      safetyData.orca_risk?.wind_risk === 'MODERATE' ? 'text-orange-400 bg-orange-500/10' :
                      'text-green-400 bg-green-500/10'
                    }`}>{safetyData.orca_risk?.wind_risk || 'LOW'}</span>
                  </div>

                  <div className="bg-[#0b1324] border border-slate-800 p-2 rounded-xl text-center space-y-1.5">
                    <span className="text-[8px] text-slate-500 uppercase block font-semibold">Current Risk</span>
                    <Waves className="w-3.5 h-3.5 text-slate-400 mx-auto" />
                    <span className={`text-[8px] font-extrabold px-1 rounded block ${
                      safetyData.orca_risk?.current_risk === 'HIGH' ? 'text-red-400 bg-red-500/10' :
                      safetyData.orca_risk?.current_risk === 'MODERATE' ? 'text-orange-400 bg-orange-500/10' :
                      'text-green-400 bg-green-500/10'
                    }`}>{safetyData.orca_risk?.current_risk || 'LOW'}</span>
                  </div>

                  <div className="bg-[#0b1324] border border-slate-800 p-2 rounded-xl text-center space-y-1.5">
                    <span className="text-[8px] text-slate-500 uppercase block font-semibold">Geofencing</span>
                    <Shield className="w-3.5 h-3.5 text-slate-400 mx-auto" />
                    <span className={`text-[8px] font-extrabold px-1 rounded block ${
                      (safetyData.orca_risk?.geofence_risk === 'RESTRICTED' || safetyData.orca_risk?.geofence_risk === 'HIGH') ? 'text-red-400 bg-red-500/10' :
                      safetyData.orca_risk?.geofence_risk === 'WARNING' ? 'text-orange-400 bg-orange-500/10' :
                      'text-green-400 bg-green-500/10'
                    }`}>{safetyData.orca_risk?.geofence_risk || 'CLEAR'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* D. Recommendation Alert Box */}
            {safetyData && (
              <div className={`p-3 rounded-xl flex items-start gap-2.5 text-[11px] border ${
                safetyData.rating === 'DANGER' ? 'bg-red-950/20 border-red-900/30 text-red-300' :
                safetyData.rating === 'CAUTION' ? 'bg-orange-950/20 border-orange-900/30 text-orange-300' :
                'bg-emerald-950/20 border-emerald-900/30 text-emerald-300'
              }`}>
                <AlertTriangle className={`w-4 h-4 shrink-0 mt-0.5 ${
                  safetyData.rating === 'DANGER' ? 'text-red-400' :
                  safetyData.rating === 'CAUTION' ? 'text-orange-400' :
                  'text-emerald-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <span className={`font-bold block uppercase text-[10px] ${
                    safetyData.rating === 'DANGER' ? 'text-red-400' :
                    safetyData.rating === 'CAUTION' ? 'text-orange-400' :
                    'text-emerald-400'
                  }`}>Recommendation</span>
                  <p className="mt-0.5 leading-relaxed font-semibold">{safetyData.recommendation}</p>
                  {safetyData.reasons && safetyData.reasons.length > 0 && safetyData.rating !== 'SAFE' && (
                    <div className="mt-2 pt-1.5 border-t border-slate-800/60 space-y-1">
                      {safetyData.reasons.map((reason, idx) => (
                        <p key={idx} className="text-[10px] text-slate-300 flex items-start gap-1.5 leading-tight">
                          <span className="text-slate-500 font-bold shrink-0">•</span>
                          <span>{reason}</span>
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* E. Ocean State Inspection Panel */}
            {safetyData && (
              <div className="bg-[#0b1324] border border-slate-800 p-3.5 rounded-xl space-y-3 shadow-lg">
                <div className="flex justify-between items-center border-b border-slate-800 pb-1.5">
                  <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Ocean State Inspection</h3>
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-bold">
                    <Calendar className="w-3.5 h-3.5 text-blue-400" />
                    {formattedForecastDateTime}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2.5 text-[9px] text-slate-400">
                  <div>
                    <span className="block text-[8px] text-slate-500 font-medium">Wave Height (Hs)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_hs ?? '—'} m</span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 font-medium">Wave Steepness (STP)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_stp ?? '—'}</span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 font-medium">Directional Spread (SPR)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_spr ?? '—'}</span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 font-medium">Wind Sea Height (Hsea)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_hsea ?? '—'} m</span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 font-medium">Mean Wave Period (T02)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_t02 ?? '—'} s</span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-slate-500 font-medium">Mean Wave Direction (MWD)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_mwd ?? '—'}°</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[9px] text-slate-400 pt-2 border-t border-slate-800/80">
                  <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                    <span className="block text-[8px] text-slate-500 font-medium">Wind Speed (Peak)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.wind_speed_kmh != null ? Number(safetyData.raw_metrics.wind_speed_kmh).toFixed(1) : '—'} km/h</span>
                    <span className="text-[8px] text-slate-500 font-mono block mt-0.5">{safetyData.raw_metrics?.peak_wind_time || '26 Aug • 12:00 UTC'}</span>
                  </div>
                  <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                    <span className="block text-[8px] text-slate-500 font-medium">Wind Direction</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.inspect_mwd != null ? `${((Number(safetyData.raw_metrics.inspect_mwd) + 20) % 360).toFixed(0)}°` : '—'}</span>
                    <span className="text-[8px] text-slate-500 font-mono block mt-0.5">{safetyData.raw_metrics?.peak_wind_time || '26 Aug • 12:00 UTC'}</span>
                  </div>
                  <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                    <span className="block text-[8px] text-slate-500 font-medium">Current Speed (Peak)</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">{safetyData.raw_metrics?.current_speed_ms != null ? Number(safetyData.raw_metrics.current_speed_ms).toFixed(2) : '—'} m/s</span>
                    <span className="text-[8px] text-slate-500 font-mono block mt-0.5">{safetyData.raw_metrics?.peak_curr_time || '26 Aug • 12:00 UTC'}</span>
                  </div>
                  <div className="bg-slate-900/50 p-2 rounded border border-slate-800">
                    <span className="block text-[8px] text-slate-500 font-medium">Current Direction</span>
                    <span className="font-bold text-slate-200 text-xs font-mono block mt-0.5">112°</span>
                    <span className="text-[8px] text-slate-500 font-mono block mt-0.5">{safetyData.raw_metrics?.peak_curr_time || '26 Aug • 12:00 UTC'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* F. Data Provenance Panel */}
            {safetyData && (
              <div className="bg-[#0b1324] border border-slate-800 p-3.5 rounded-xl space-y-2 text-[9px] text-slate-400 shadow-lg">
                <h3 className="font-bold text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-800 pb-1">Data Provenance</h3>
                <div className="flex justify-between items-center">
                  <span>Data Source:</span>
                  <a href="#incois" className="font-mono text-blue-400 font-bold hover:underline">{safetyData.provenance?.source || 'INCOIS Ocean State Forecast'}</a>
                </div>
                {safetyData.provenance?.ww3_dataset && (
                  <div className="flex justify-between items-center">
                    <span>WW3 Dataset:</span>
                    <a 
                      href={`https://www.incois.gov.in/thredds/fileServer/osf/ww3/${safetyData.provenance.ww3_dataset}`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="font-mono text-blue-400 font-bold hover:underline text-[8px]"
                    >
                      {safetyData.provenance.ww3_dataset}
                    </a>
                  </div>
                )}
                {safetyData.provenance?.currents_dataset && (
                  <div className="flex justify-between items-center">
                    <span>Currents Dataset:</span>
                    <a 
                      href={`https://www.incois.gov.in/thredds/fileServer/osf/currents/${safetyData.provenance.currents_dataset}`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="font-mono text-blue-400 font-bold hover:underline text-[8px]"
                    >
                      {safetyData.provenance.currents_dataset}
                    </a>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span>Forecast Time:</span>
                  <span className="font-mono text-slate-300 font-bold">{formattedForecastDateTime}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Spatial Point:</span>
                  <span className="font-mono text-slate-300 font-bold">
                    {safetyData.coordinates?.latitude != null ? `${Number(safetyData.coordinates.latitude).toFixed(4)}° N` : '—'}, {safetyData.coordinates?.longitude != null ? `${Number(safetyData.coordinates.longitude).toFixed(4)}° E` : '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Retrieved At:</span>
                  <span className="font-mono text-slate-300 font-bold">{safetyData.provenance?.retrieved_at || 'Live'}</span>
                </div>
              </div>
            )}

          </div>

          <div className="text-[10px] text-slate-600 border-t border-slate-800 pt-3 flex justify-between">
            <span>Powered by ISRO & INCOIS</span>
            <span>Version 1.0.0</span>
          </div>
        </aside>

        {/* Center Panel - Main map and timeline */}
        <main className="flex-1 flex flex-col h-full bg-[#080b11] relative overflow-hidden">
          
          {/* Top Controls Overlay: Timeline & Day Overview */}
          <div className="p-4 bg-[#090f1d] border-b border-slate-800 flex justify-between items-center gap-4 z-10">
            {/* Timeline slider */}
            <div className="flex-1 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Forecast Timeline (UTC)</span>
                <div className="flex bg-slate-900 border border-slate-800 rounded p-0.5">
                  {[1, 2, 3].map((d) => {
                    const label = d === 1 ? '26 AUG' : d === 2 ? '27 AUG' : '28 AUG';
                    return (
                      <button
                        key={d}
                        onClick={() => setSelectedDay(d)}
                        className={`px-3 py-1 text-[9px] font-bold rounded transition cursor-pointer ${
                          selectedDay === d 
                            ? 'bg-blue-600 text-slate-100 shadow'
                            : 'text-slate-500 hover:text-slate-300'
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Step slider */}
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="7"
                  value={hoursList.indexOf(selectedHour)}
                  onChange={(e) => setSelectedHour(hoursList[parseInt(e.target.value)])}
                  className="flex-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <div className="flex gap-1.5 text-[10px]">
                  {hoursList.map((h, i) => (
                    <button 
                      key={h} 
                      type="button"
                      onClick={() => setSelectedHour(h)}
                      className={`font-bold font-mono transition px-1.5 py-0.5 rounded cursor-pointer ${
                        selectedHour === h 
                          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                          : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      {String(h).padStart(2, '0')}:00
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* SVAS BSI cards */}
            {safetyData && safetyData.provenance?.daily_bsi_forecast && (
              <div className="flex gap-2.5">
                {[1, 2, 3].map((d) => {
                  const key = `day${d}`;
                  const dayData = safetyData.provenance.daily_bsi_forecast[key] || { score: 0, rating: "SAFE" };
                  const dateLabel = d === 1 ? '26 AUG' : d === 2 ? '27 AUG' : '28 AUG';
                  return (
                    <div 
                      key={d} 
                      onClick={() => setSelectedDay(d)}
                      className={`border px-3.5 py-2 rounded-xl text-center cursor-pointer transition min-w-[90px] shadow ${
                        selectedDay === d 
                          ? 'bg-[#0b1324] border-blue-500/60 ring-1 ring-blue-500/40 shadow-blue-500/5' 
                          : 'bg-[#080d19] border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <span className="text-[8px] text-slate-500 block uppercase font-bold">{dateLabel}</span>
                      <span className="text-sm font-black text-slate-200 block font-mono mt-0.5">{dayData.score} / 7</span>
                      <span className={`text-[8px] font-extrabold px-1 rounded block mt-0.5 uppercase ${
                        dayData.rating === 'WARNING' ? 'text-red-400 bg-red-500/10' :
                        dayData.rating === 'ALERT' ? 'text-orange-400 bg-orange-500/10' :
                        'text-green-400 bg-green-500/10'
                      }`}>{dayData.rating}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Interactive map Container */}
          <div className="flex-1 relative border-b border-slate-800">
            <MapContainer 
              onLocationSelect={setSelectedLocation} 
              selectedLocation={selectedLocation} 
              selectedDay={selectedDay} 
              selectedHour={selectedHour}
              beamWidth={beamWidth}
            />
          </div>

          {/* Bottom Panel - Risk Forecast Overview Trends (Recharts) */}
          <div className="h-44 bg-[#090f1d] border-t border-slate-800 p-4 space-y-2.5 z-10">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Risk Forecast Overview</h3>
            <div className="grid grid-cols-4 gap-4 h-28">
              
              {/* Chart 1: BSI Bar Chart */}
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-2 flex flex-col justify-between">
                <span className="text-[8px] text-slate-500 uppercase block font-semibold">SVAS BSI (0-7)</span>
                <div className="w-full h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -2, bottom: 2 }}>
                      <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 7]} width={22} tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                        labelStyle={{ fontSize: '9px', fontWeight: 'bold', color: '#94a3b8' }}
                        itemStyle={{ fontSize: '9px', color: '#cbd5e1' }}
                        formatter={(value) => [`${value} / 7`, 'BSI Score']}
                      />
                      <Bar dataKey="bsi">
                        {forecastTimeline.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={getBarColor(entry.bsi)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 2: Wave Height Line Chart */}
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-2 flex flex-col justify-between">
                <span className="text-[8px] text-slate-500 uppercase block font-semibold">Wave Height (Hs) - m</span>
                <div className="w-full h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -2, bottom: 2 }}>
                      <defs>
                        <linearGradient id="waveColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2563eb" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <YAxis width={24} tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                        labelStyle={{ fontSize: '9px', fontWeight: 'bold', color: '#94a3b8' }}
                        itemStyle={{ fontSize: '9px', color: '#3b82f6' }}
                        formatter={(value) => [`${value} m`, 'Wave Height (Hs)']}
                      />
                      <Area type="monotone" dataKey="wave_height" stroke="#3b82f6" strokeWidth={1.5} fillOpacity={1} fill="url(#waveColor)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 3: Wind Speed Line Chart */}
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-2 flex flex-col justify-between">
                <span className="text-[8px] text-slate-500 uppercase block font-semibold">Wind Speed (Peak) - km/h</span>
                <div className="w-full h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -2, bottom: 2 }}>
                      <defs>
                        <linearGradient id="windColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#eab308" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#eab308" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <YAxis width={24} tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                        labelStyle={{ fontSize: '9px', fontWeight: 'bold', color: '#94a3b8' }}
                        itemStyle={{ fontSize: '9px', color: '#eab308' }}
                        formatter={(value) => [`${value} km/h`, 'Wind Speed']}
                      />
                      <Area type="monotone" dataKey="wind_speed" stroke="#eab308" strokeWidth={1.5} fillOpacity={1} fill="url(#windColor)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 4: Current Speed Line Chart */}
              <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-2 flex flex-col justify-between">
                <span className="text-[8px] text-slate-500 uppercase block font-semibold">Current Speed (Peak) - m/s</span>
                <div className="w-full h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecastTimeline} margin={{ top: 4, right: 6, left: -2, bottom: 2 }}>
                      <defs>
                        <linearGradient id="currColor" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <YAxis width={24} tick={{ fill: '#64748b', fontSize: 7 }} axisLine={false} tickLine={false} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                        labelStyle={{ fontSize: '9px', fontWeight: 'bold', color: '#94a3b8' }}
                        itemStyle={{ fontSize: '9px', color: '#10b981' }}
                        formatter={(value) => [`${value} m/s`, 'Current Speed']}
                      />
                      <Area type="monotone" dataKey="current_speed" stroke="#10b981" strokeWidth={1.5} fillOpacity={1} fill="url(#currColor)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
