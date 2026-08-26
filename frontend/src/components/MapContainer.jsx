import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

function MapContainer({ onLocationSelect, selectedLocation, selectedDay, beamWidth }) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  // Helper to map continuous beam width to official INCOIS category suffix
  const getSuffix = (width) => {
    if (width < 4.0) return '4';
    if (width < 6.0) return '6';
    return '7';
  };

  // Sync map colors when selectedDay or beamWidth changes
  useEffect(() => {
    if (mapRef.current && mapRef.current.getLayer('advisory-fill')) {
      const suffix = getSuffix(beamWidth);
      mapRef.current.setPaintProperty('advisory-fill', 'fill-color', [
        'case',
        ['==', ['get', `Color${suffix}`], 'orange'], '#f97316',
        ['==', ['get', `Color${suffix}`], 'red'], '#ef4444',
        '#22c55e'
      ]);
      mapRef.current.setPaintProperty('advisory-stroke', 'line-color', [
        'case',
        ['==', ['get', `Color${suffix}`], 'orange'], '#fb923c',
        ['==', ['get', `Color${suffix}`], 'red'], '#f87171',
        '#4ade80'
      ]);
    }
  }, [selectedDay, beamWidth]);

  useEffect(() => {
    if (mapRef.current) return; // Initialize only once

    // Initialize MapLibre GL
    mapRef.current = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', // Dark themed base map
      center: [82.0, 16.0], // Centered around the Bay of Bengal / India Coast
      zoom: 5,
    });

    mapRef.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    mapRef.current.on('load', async () => {
      try {
        // Fetch the live INCOIS advisory polygons via our local CORS proxy
        const response = await fetch('http://localhost:8000/api/safety/advisories');
        if (!response.ok) throw new Error('Advisory fetch failed');
        const geojson = await response.json();

        // Add the GeoJSON source to MapLibre
        mapRef.current.addSource('coastal-advisories', {
          type: 'geojson',
          data: geojson
        });

        const suffix = getSuffix(beamWidth);

        // Renders the buffer polygon fields colored by warning status for the selectedDay
        mapRef.current.addLayer({
          id: 'advisory-fill',
          type: 'fill',
          source: 'coastal-advisories',
          paint: {
            'fill-color': [
              'case',
              ['==', ['get', `Color${suffix}`], 'orange'], '#f97316',     // Orange for Alert
              ['==', ['get', `Color${suffix}`], 'red'], '#ef4444',        // Red for Warning
              '#22c55e'                                                   // Green for Safe
            ],
            'fill-opacity': 0.35
          }
        });

        // Add borders to the coastal polygons
        mapRef.current.addLayer({
          id: 'advisory-stroke',
          type: 'line',
          source: 'coastal-advisories',
          paint: {
            'line-color': [
              'case',
              ['==', ['get', `Color${suffix}`], 'orange'], '#fb923c',
              ['==', ['get', `Color${suffix}`], 'red'], '#f87171',
              '#4ade80'
            ],
            'line-width': 1.2
          }
        });

        // Add click listener on the advisory polygons to show details popup
        mapRef.current.on('click', 'advisory-fill', (e) => {
          const features = mapRef.current.queryRenderedFeatures(e.point, { layers: ['advisory-fill'] });
          if (!features.length) return;
          const feature = features[0];
          const props = feature.properties;
          
          const district = props.DistrictNa || props.ENG || props.name || "Coastal Strip";
          const state = props.state || "";
          
          // Determine boat size category based on current beamWidth selection
          const currentSuffix = getSuffix(beamWidth);
          const limitStr = currentSuffix === '4' ? '4m' : currentSuffix === '6' ? '6m' : '7m';
          
          // Parse dynamic HTML advisory content directly from INCOIS dataset properties
          let advisoryText = props[`ENG${currentSuffix}`] || props[`HIN${currentSuffix}`] || props.Advisory_E || "";
          advisoryText = advisoryText.trim();
          
          // If empty and region is green, default to the official dynamic Safe advisory sentence
          if (!advisoryText) {
            const warningColor = props[`Color${currentSuffix}`];
            if (warningColor === 'Green' || warningColor === 'Safe' || !warningColor) {
              advisoryText = `${district} district, Boats less than ${limitStr} wide can safely sail.`;
            } else {
              advisoryText = "No advisory details available.";
            }
          }
          
          // Clean up raw HTML: remove INCOIS image logo, trim leading breaks, and shrink text sizes
          const cleanedAdvisory = advisoryText
            .replace(/<img[^>]*>/gi, '') // Remove INCOIS logo
            .replace(/^(\s*<br\s*\/?>\s*)+/i, '') // Remove leading line breaks
            .replace(/font-size\s*:\s*[^;']*(px|rem|em)?/gi, 'font-size: 11px') // Standardize fonts to 11px
            .replace(/line-height\s*:\s*[^;']*(px|rem|em)?/gi, 'line-height: 1.3') // Standardize line spacing
            .trim();
          
          new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="text-slate-900 p-2 font-sans space-y-1.5" style="max-width: 360px;">
                <h4 class="font-bold border-b pb-1 text-blue-600 text-xs">${district} (${state})</h4>
                <div class="text-[9px] text-slate-500 font-bold">Source: INCOIS</div>
                <div class="text-[11px] leading-relaxed text-slate-700 mt-1">${cleanedAdvisory}</div>
              </div>
            `)
            .addTo(mapRef.current);
        });

        // Change the cursor to a pointer when hovering over the advisory layer
        mapRef.current.on('mouseenter', 'advisory-fill', () => {
          mapRef.current.getCanvas().style.cursor = 'pointer';
        });
        mapRef.current.on('mouseleave', 'advisory-fill', () => {
          mapRef.current.getCanvas().style.cursor = '';
        });

        // 3. Fetch the geofencing (EEZ & MPA) boundary layers from our API
        const geofenceRes = await fetch('http://localhost:8000/api/geofence/geojson');
        if (geofenceRes.ok) {
          const geofenceGeojson = await geofenceRes.json();
          
          mapRef.current.addSource('geofencing-layers', {
            type: 'geojson',
            data: geofenceGeojson
          });

          // Renders Marine Protected Area (MPA) restricted zones
          mapRef.current.addLayer({
            id: 'mpa-fill',
            type: 'fill',
            source: 'geofencing-layers',
            filter: ['==', ['get', 'type'], 'MPA'],
            paint: {
              'fill-color': '#f43f5e',
              'fill-opacity': 0.2
            }
          });

          mapRef.current.addLayer({
            id: 'mpa-stroke',
            type: 'line',
            source: 'geofencing-layers',
            filter: ['==', ['get', 'type'], 'MPA'],
            paint: {
              'line-color': '#e11d48',
              'line-width': 1.5,
              'line-dasharray': [2, 2]
            }
          });

          // Renders Indian EEZ Border outline
          mapRef.current.addLayer({
            id: 'eez-stroke',
            type: 'line',
            source: 'geofencing-layers',
            filter: ['==', ['get', 'type'], 'EEZ'],
            paint: {
              'line-color': '#ef4444',
              'line-width': 2.0,
              'line-dasharray': [4, 4]
            }
          });

          // Click listener to identify specific Marine Protected Areas
          mapRef.current.on('click', 'mpa-fill', (e) => {
            const mpaFeatures = mapRef.current.queryRenderedFeatures(e.point, { layers: ['mpa-fill'] });
            if (!mpaFeatures.length) return;
            const name = mpaFeatures[0].properties.name;
            
            new maplibregl.Popup()
              .setLngLat(e.lngLat)
              .setHTML(`
                <div class="text-slate-900 p-2 font-sans space-y-1" style="max-width: 260px;">
                  <h4 class="font-bold border-b pb-1 text-red-600 text-xs">Restricted Zone</h4>
                  <p class="text-[10px] text-slate-700 leading-relaxed font-semibold mt-1">
                    ${name}<br>
                    <span class="text-[9px] text-slate-500 font-normal">Sailing or fishing inside this marine sanctuary is strictly prohibited.</span>
                  </p>
                </div>
              `)
              .addTo(mapRef.current);
          });

          // Hover cursor styling for restricted sanctuaries
          mapRef.current.on('mouseenter', 'mpa-fill', () => {
            mapRef.current.getCanvas().style.cursor = 'pointer';
          });
          mapRef.current.on('mouseleave', 'mpa-fill', () => {
            mapRef.current.getCanvas().style.cursor = '';
          });
        }

      } catch (err) {
        console.error('Error loading map data layers:', err);
      }
    });

    // Handle clicks to select inspect coordinates (works inside polygons too)
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

  // Update the map marker whenever the selected coordinates change
  useEffect(() => {
    if (!mapRef.current) return;

    if (selectedLocation) {
      const coords = [selectedLocation.lon, selectedLocation.lat];

      if (markerRef.current) {
        // Move existing marker
        markerRef.current.setLngLat(coords);
      } else {
        // Create a new custom boat SVG marker
        const el = document.createElement('div');
        el.className = 'marker';
        el.style.width = '30px';
        el.style.height = '36px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" width="100%" height="100%">
            <defs>
              <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000000" flood-opacity="0.3"/>
              </filter>
              <linearGradient id="pinGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#0284C7"/>
                <stop offset="100%" stop-color="#0369A1"/>
              </linearGradient>
            </defs>
            <!-- Map Pin Body (Includes the main tip pointing to coordinates) -->
            <path d="M 50 10 
                     C 25 10, 10 28, 10 52 
                     C 10 76, 38 102, 50 112 
                     C 62 102, 90 76, 90 52 
                     C 90 28, 75 10, 50 10 Z" 
                  fill="url(#pinGradient)" 
                  stroke="#FFFFFF" 
                  stroke-width="3.5" 
                  filter="url(#shadow)"/>
            <!-- Sailboat Icon (Omitted the white circle background completely!) -->
            <g transform="translate(0, 2)">
              <path d="M 48 26 L 48 53 L 67 53 C 67 53, 68 37, 48 26 Z" fill="#FFFFFF"/>
              <path d="M 44 31 L 44 53 L 33 53 C 33 53, 35 40, 44 31 Z" fill="#38BDF8"/>
              <line x1="46" y1="24" x2="46" y2="55" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M 28 57 L 72 57 L 65 67 C 60 70, 40 70, 35 67 Z" fill="#E2E8F0"/>
              <path d="M 25 68 Q 30 66, 35 68 T 45 68 T 55 68 T 65 68 T 75 68" 
                    fill="none" 
                    stroke="#38BDF8" 
                    stroke-width="2" 
                    stroke-linecap="round"/>
            </g>
          </svg>
        `;

        markerRef.current = new maplibregl.Marker({ element: el })
          .setLngLat(coords)
          .addTo(mapRef.current);
      }

      // Smooth pan to clicked coordinate
      mapRef.current.easeTo({ center: coords });
    } else {
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }
    }
  }, [selectedLocation]);

  return (
    <div className="w-full h-full relative">
      <div ref={mapContainerRef} className="w-full h-full" />
      <div className="absolute top-4 left-4 bg-slate-900/90 p-4 rounded-xl border border-slate-700 text-xs shadow-lg space-y-2">
        <h3 className="font-bold text-blue-400">Map Legend</h3>
        <div className="flex flex-col gap-1.5 text-[10px] text-slate-300">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-500/40 border border-red-500" />
            <span>WARNING (Rough seas / Storm)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-orange-500/40 border border-orange-500" />
            <span>ALERT (Compounding wave hazards)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-500/40 border border-green-500" />
            <span>SAFE (Optimal fishing conditions)</span>
          </div>
          <div className="flex items-center gap-2 border-t border-slate-700/50 pt-1 mt-0.5">
            <div className="w-3 h-0.5 border-t-2 border-dashed border-red-500" />
            <span>Indian EEZ Border (Border Crossing Warning)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-rose-500/20 border border-rose-500 border-dashed" />
            <span>Restricted MPA (No-Fishing Sanctuary)</span>
          </div>
        </div>
        <p className="text-[10px] text-slate-500 italic mt-2 border-t border-slate-700/50 pt-1.5">
          Left-click anywhere to inspect coordinates.
        </p>
      </div>
    </div>
  );
}

export default MapContainer;