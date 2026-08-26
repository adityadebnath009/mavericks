import React, { useState, useEffect } from 'react';
import MapContainer from './components/MapContainer';

function App() {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [beamWidth, setBeamWidth] = useState(3.5);
  const [selectedDay, setSelectedDay] = useState(1);
  const [safetyData, setSafetyData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch safety calculations from backend proxy
  const fetchSafetyAssessment = async (lat, lon, beam, day) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `http://localhost:8000/api/safety/?lat=${lat}&lon=${lon}&beam=${beam}&day=${day}`
      );
      if (!response.ok) {
        throw new Error('Failed to retrieve safety assessment from backend.');
      }
      const data = await response.json();
      setSafetyData(data);
    } catch (err) {
      setError(err.message);
      setSafetyData(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Re-fetch whenever location, beam width, or forecast day changes
  useEffect(() => {
    if (selectedLocation) {
      fetchSafetyAssessment(selectedLocation.lat, selectedLocation.lon, beamWidth, selectedDay);
    }
  }, [selectedLocation, beamWidth, selectedDay]);

  // Status color helpers
  const getStatusColor = (rating) => {
    if (rating === 'SAFE') return 'text-green-400 border-green-500 bg-green-500/10';
    if (rating === 'CAUTION') return 'text-orange-400 border-orange-500 bg-orange-500/10';
    return 'text-red-400 border-red-500 bg-red-500/10';
  };

  return (
    <div className="flex h-screen w-screen bg-slate-900 text-white overflow-hidden font-sans">
      {/* Sidebar - Controls & Safety Assessment Card */}
      <div className="w-1/3 h-full bg-slate-800 p-6 border-r border-slate-700 flex flex-col justify-between overflow-y-auto">
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-blue-400">ORCA Portal</h1>
            <p className="text-xs text-slate-400 mb-4">Intelligent Marine Decision-Support System</p>
            
            {/* Day Selector Tabs */}
            <div className="flex bg-slate-900/50 p-1 rounded-lg border border-slate-700">
              {[1, 2, 3].map((d) => {
                const date = new Date();
                date.setDate(date.getDate() + (d - 1));
                const dd = String(date.getDate()).padStart(2, '0');
                const mm = String(date.getMonth() + 1).padStart(2, '0');
                const yyyy = date.getFullYear();
                const dateStr = `${dd}-${mm}-${yyyy}`;
                return (
                  <button
                    key={d}
                    onClick={() => setSelectedDay(d)}
                    className={`flex-1 py-1.5 text-[9px] font-bold rounded-md transition ${
                      selectedDay === d
                        ? 'bg-blue-600 text-white shadow'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Day {d} ({dateStr})
                  </button>
                );
              })}
            </div>
          </div>

          {/* 1. Vessel Profile Card */}
          <div className="bg-slate-750 p-4 rounded-xl border border-slate-700 shadow-lg space-y-4">
            <h2 className="text-sm font-semibold text-blue-300">Vessel Digital Profile</h2>
            
            <div className="space-y-1.5 text-xs">
              <label className="text-slate-400">Vessel Type:</label>
              <select
                value={Math.abs(beamWidth - 2.5) < 0.2 ? "traditional" : Math.abs(beamWidth - 4.5) < 0.2 ? "small_trawler" : "large_trawler"}
                onChange={(e) => {
                  const type = e.target.value;
                  if (type === "traditional") setBeamWidth(2.5);
                  else if (type === "small_trawler") setBeamWidth(4.5);
                  else setBeamWidth(6.5);
                }}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="traditional">Traditional Fishing Vessel (&lt;10m length)</option>
                <option value="small_trawler">Small Mechanized Trawler</option>
                <option value="large_trawler">Large Trawler / Deep-sea Vessel</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs text-slate-400 flex justify-between">
                <span>Vessel Beam Width (m):</span>
                <span className="font-mono text-blue-400 font-bold">{beamWidth.toFixed(1)}m</span>
              </label>
              <input
                type="range"
                min="1.0"
                max="8.0"
                step="0.1"
                value={beamWidth}
                onChange={(e) => setBeamWidth(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <div className="space-y-1">
              <span className="text-[10px] text-slate-400">SVAS Advisory Beam Category:</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setBeamWidth(2.5)}
                  className={`flex-1 text-[10px] p-1.5 rounded border transition text-center font-bold ${
                    beamWidth < 4.0
                      ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                      : 'border-slate-800 text-slate-500 bg-slate-850 cursor-not-allowed'
                  }`}
                  disabled={beamWidth >= 4.0}
                >
                  ● &lt;4 m
                </button>
                <button
                  onClick={() => setBeamWidth(4.5)}
                  className={`flex-1 text-[10px] p-1.5 rounded border transition text-center font-bold ${
                    beamWidth >= 4.0 && beamWidth < 6.0
                      ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                      : 'border-slate-800 text-slate-500 bg-slate-850 cursor-not-allowed'
                  }`}
                  disabled={beamWidth < 4.0 || beamWidth >= 6.0}
                >
                  ● &lt;6 m
                </button>
                <button
                  onClick={() => setBeamWidth(6.5)}
                  className={`flex-1 text-[10px] p-1.5 rounded border transition text-center font-bold ${
                    beamWidth >= 6.0
                      ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                      : 'border-slate-800 text-slate-500 bg-slate-850 cursor-not-allowed'
                  }`}
                  disabled={beamWidth < 6.0}
                >
                  ● &lt;7 m
                </button>
              </div>
            </div>
          </div>

          {/* 2. Safety Assessment Output */}
          <div className="space-y-4">
            <h2 className="text-sm font-semibold text-slate-300">Safety Inspection Details</h2>
            
            {isLoading && (
              <p className="text-xs text-slate-400 animate-pulse">Running spatial analysis & fetching weather parameters...</p>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-3 rounded-lg">
                Error: {error}
              </div>
            )}

            {!selectedLocation && !isLoading && (
              <p className="text-xs text-slate-500 italic">Click on any coastal region on the map to trigger a safety assessment.</p>
            )}

            {safetyData && !isLoading && (
              <div className="space-y-4">
                {/* Overall Status Badge */}
                <div className="bg-slate-750 p-4 rounded-xl border border-slate-700/60 shadow-md">
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Overall ORCA Status</span>
                      <span className={`inline-block text-sm font-black px-3.5 py-1.5 rounded-full border mt-1 shadow-sm ${
                        safetyData.orca_risk.overall_status === 'HIGH' ? 'text-red-400 border-red-500/40 bg-red-500/10' :
                        safetyData.orca_risk.overall_status === 'MODERATE' ? 'text-orange-400 border-orange-500/40 bg-orange-500/10' :
                        'text-green-400 border-green-500/40 bg-green-500/10'
                      }`}>
                        {safetyData.orca_risk.overall_status === 'HIGH' ? '⚠ DANGER (High Risk)' :
                         safetyData.orca_risk.overall_status === 'MODERATE' ? '⚠ CAUTION (Moderate Risk)' :
                         '✓ SAFE (Low Risk)'}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[9px] text-slate-400 uppercase tracking-wider block">Coordinates</span>
                      <p className="text-[11px] font-mono text-slate-200 mt-1 font-bold">
                        {safetyData.coordinates.latitude.toFixed(4)}°N, {safetyData.coordinates.longitude.toFixed(4)}°E
                      </p>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-slate-850 p-4 rounded-xl border border-slate-700 text-xs">
                  <h3 className="font-bold text-slate-300">Operational Decision Support:</h3>
                  <p className="mt-1.5 text-slate-200 leading-relaxed font-medium">{safetyData.recommendation}</p>
                </div>

                {/* Explanation Breakdown: "WHY THIS DECISION?" */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Why this decision?</h3>
                  <div className="bg-slate-850/40 border border-slate-700/50 rounded-xl p-3.5 space-y-2.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-300">SVAS Capsizing Risk:</span>
                      <span className={`font-black px-2 py-0.5 rounded text-[10px] ${
                        safetyData.bsi_metrics.rating === 'WARNING' ? 'text-red-400 bg-red-500/10 border border-red-500/30' :
                        safetyData.bsi_metrics.rating === 'ALERT' ? 'text-orange-400 bg-orange-500/10 border border-orange-500/30' :
                        'text-green-400 bg-green-500/10 border border-green-500/30'
                      }`}>
                        {safetyData.bsi_metrics.rating} ({safetyData.bsi_metrics.bsi_score}/7 BSI)
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-300">Wind Risk Layer:</span>
                      <span className={`font-black px-2 py-0.5 rounded text-[10px] ${
                        safetyData.orca_risk.wind_risk === 'HIGH' ? 'text-red-400 bg-red-500/10 border border-red-500/30' :
                        safetyData.orca_risk.wind_risk === 'MODERATE' ? 'text-orange-400 bg-orange-500/10 border border-orange-500/30' :
                        'text-green-400 bg-green-500/10 border border-green-500/30'
                      }`}>
                        {safetyData.orca_risk.wind_risk}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-300">Currents Risk Layer:</span>
                      <span className={`font-black px-2 py-0.5 rounded text-[10px] ${
                        safetyData.orca_risk.current_risk === 'HIGH' ? 'text-red-400 bg-red-500/10 border border-red-500/30' :
                        safetyData.orca_risk.current_risk === 'MODERATE' ? 'text-orange-400 bg-orange-500/10 border border-orange-500/30' :
                        'text-green-400 bg-green-500/10 border border-green-500/30'
                      }`}>
                        {safetyData.orca_risk.current_risk}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-slate-300">Geofencing Constraints:</span>
                      <span className={`font-black px-2 py-0.5 rounded text-[10px] ${
                        safetyData.orca_risk.geofence_risk === 'HIGH' ? 'text-red-400 bg-red-500/10 border border-red-500/30' :
                        safetyData.orca_risk.geofence_risk === 'MODERATE' ? 'text-orange-400 bg-orange-500/10 border border-orange-500/30' :
                        'text-green-400 bg-green-500/10 border border-green-500/30'
                      }`}>
                        {safetyData.orca_risk.geofence_risk}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Warning Details List */}
                {safetyData.reasons && safetyData.reasons.length > 0 && (
                  <div className="space-y-1.5">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Alerts & Thresholds:</h3>
                    <ul className="list-disc pl-4 text-[11px] text-slate-300 space-y-1.5">
                      {safetyData.reasons.map((r, i) => (
                        <li key={i} className="leading-normal">{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Detailed Wave, Wind, Current Inspection Parameters */}
                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/60 space-y-3">
                  <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider">Ocean State Inspection Details</h3>
                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="bg-slate-800 p-2.5 rounded border border-slate-700/40">
                      <span className="text-slate-400 block font-medium">BSI Wave Score:</span>
                      <span className="font-bold text-slate-200 text-xs font-mono">{safetyData.bsi_metrics.bsi_score} / 7</span>
                    </div>
                    <div className="bg-slate-800 p-2.5 rounded border border-slate-700/40">
                      <span className="text-slate-400 block font-medium">Wave Height (Hs):</span>
                      <span className="font-bold text-slate-200 text-xs font-mono">{safetyData.raw_metrics.wave_height_m.toFixed(2)} m</span>
                    </div>
                    <div className="bg-slate-800 p-2.5 rounded border border-slate-700/40">
                      <span className="text-slate-400 block font-medium">Wave Steepness:</span>
                      <span className="font-bold text-slate-200 text-xs font-mono">{safetyData.bsi_metrics.wave_steepness}</span>
                    </div>
                    <div className="bg-slate-800 p-2.5 rounded border border-slate-700/40">
                      <span className="text-slate-400 block font-medium">Directional Spread:</span>
                      <span className="font-bold text-slate-200 text-xs font-mono">{safetyData.bsi_metrics.directional_spread}</span>
                    </div>
                    <div className="bg-slate-800 p-2.5 rounded border border-slate-700/40">
                      <span className="text-slate-400 block font-medium">Wind Speed (Peak):</span>
                      <span className="font-bold text-slate-200 text-xs font-mono">{safetyData.raw_metrics.wind_speed_kmh.toFixed(1)} km/h</span>
                    </div>
                    <div className="bg-slate-800 p-2.5 rounded border border-slate-700/40">
                      <span className="text-slate-400 block font-medium font-medium">Current Speed (Peak):</span>
                      <span className="font-bold text-slate-200 text-xs font-mono">{safetyData.raw_metrics.current_speed_ms.toFixed(2)} m/s</span>
                    </div>
                  </div>
                </div>

                {/* Data Status Freshness Panel */}
                <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3 text-[10px] text-slate-400 space-y-1.5">
                  <h3 className="font-bold text-slate-400 uppercase text-[9px] tracking-wider">Data Ingestion Status</h3>
                  <div className="flex justify-between items-center">
                    <span>Data Source:</span>
                    <span className="font-mono text-slate-300 font-bold">{safetyData.provenance.source}</span>
                  </div>
                  {safetyData.provenance.ww3_dataset && (
                    <div className="flex justify-between items-center">
                      <span>WW3 Dataset:</span>
                      <span className="font-mono text-blue-400 font-bold text-[9px]">{safetyData.provenance.ww3_dataset}</span>
                    </div>
                  )}
                  {safetyData.provenance.currents_dataset && (
                    <div className="flex justify-between items-center">
                      <span>Currents Dataset:</span>
                      <span className="font-mono text-blue-400 font-bold text-[9px]">{safetyData.provenance.currents_dataset}</span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span>Timestamp Verified:</span>
                    <span className="font-mono text-slate-300 font-bold">{safetyData.provenance.retrieved_at}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="text-[10px] text-slate-500 border-t border-slate-700 pt-4 flex justify-between">
          <span>Powered by ISRO & INCOIS</span>
          <span>Version 1.0.0</span>
        </div>
      </div>

      {/* Main Panel - Interactive Map */}
      <div className="w-2/3 h-full relative">
        <MapContainer 
          onLocationSelect={setSelectedLocation} 
          selectedLocation={selectedLocation} 
          selectedDay={selectedDay} 
          beamWidth={beamWidth}
        />
      </div>
    </div>
  );
}

export default App;
