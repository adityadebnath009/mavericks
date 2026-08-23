import React, { useState } from 'react';
import MapContainer from './components/MapContainer';

function App() {
  const [selectedLocation, setSelectedLocation] = useState(null);

  return (
    <div className="flex h-screen w-screen bg-slate-900 text-white overflow-hidden font-sans">
      {/* Sidebar - Controls, Safety Score, Chat, Routing */}
      <div className="w-1/4 h-full bg-slate-800 p-4 border-r border-slate-700 flex flex-col justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-blue-400">ORCA Portal</h1>
          <p className="text-xs text-slate-400 mb-6">Marine Intelligence & Safety Dashboard</p>
          
          <div className="bg-slate-700 p-4 rounded-lg mb-4">
            <h2 className="text-sm font-semibold mb-2">Selected Location</h2>
            {selectedLocation ? (
              <p className="text-xs text-slate-300">
                Lat: {selectedLocation.lat.toFixed(4)}, Lon: {selectedLocation.lon.toFixed(4)}
              </p>
            ) : (
              <p className="text-xs text-slate-400">Click on the map to inspect coordinates</p>
            )}
          </div>
        </div>

        <div className="text-xs text-slate-500 border-t border-slate-700 pt-4">
          Powered by ISRO, INCOIS & Open-Meteo
        </div>
      </div>

      {/* Main Panel - Map & Timeline */}
      <div className="w-3/4 h-full relative">
        <MapContainer onLocationSelect={setSelectedLocation} />
      </div>
    </div>
  );
}

export default App;
