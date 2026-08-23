import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

function MapContainer({ onLocationSelect }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    if (mapRef.current) return; // Only initialize once

    // Initialize MapLibre GL JS map instance
    mapRef.current = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://demotiles.maplibre.org/style.json', // Basic default style
      center: [79.0, 9.0], // Centered around Palk Strait / Southern India
      zoom: 6,
    });

    // Add navigation controls (zoom, compass)
    mapRef.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    // Handle click interactions to fetch coordinate inspectors
    mapRef.current.on('click', (e) => {
      const { lng, lat } = e.lngLat;
      if (onLocationSelect) {
        onLocationSelect({ lat, lon: lng });
      }
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [onLocationSelect]);

  return (
    <div className="w-full h-full relative">
      <div ref={mapContainerRef} className="w-full h-full" />
      <div className="absolute top-4 left-4 bg-slate-900/80 p-3 rounded-lg border border-slate-700 text-xs shadow-md">
        <h3 className="font-semibold text-blue-400">Map Legend</h3>
        <p className="mt-1 text-slate-300">Left-click to inspect points</p>
      </div>
    </div>
  );
}

export default MapContainer;
