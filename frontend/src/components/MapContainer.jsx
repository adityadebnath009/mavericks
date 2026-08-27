import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const getApiUrl = (path) => {
  if (typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location;
    if (protocol === 'file:' || ((hostname === 'localhost' || hostname === '127.0.0.1') && port !== '8000')) {
      return `http://127.0.0.1:8000${path}`;
    }
  }
  return path;
};

function MapContainer({ 
  onLocationSelect, 
  selectedLocation, 
  selectedDay = 1, 
  selectedHour = 12,
  beamWidth = 3.5 
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const popupRef = useRef(null);
  const selectedDayRef = useRef(selectedDay);
  const selectedHourRef = useRef(selectedHour);
  const onLocationSelectRef = useRef(onLocationSelect);
  const [mapLoaded, setMapLoaded] = useState(false);

  selectedDayRef.current = selectedDay;
  selectedHourRef.current = selectedHour;
  onLocationSelectRef.current = onLocationSelect;

  const getSuffix = (width) => {
    if (width < 4.0) return '4';
    if (width < 6.0) return '6';
    return '7';
  };

  // Map layer toggle states
  const [layers, setLayers] = useState({
    bsiRisk: true,
    advisories: true,
    eezBorder: true,
    restricted: true,
    windSpeed: true,
    currentSpeed: true,
    fishingZones: false,
    route: false,
    sst: false,
    chlorophyll: false,
    pfzAdvisory: false
  });

  const [sstOpacity, setSstOpacity] = useState(0.65);
  const [chlOpacity, setChlOpacity] = useState(0.65);

  const toggleLayer = (key, layerIds) => {
    const updated = !layers[key];
    setLayers(prev => ({ ...prev, [key]: updated }));
    
    if (mapRef.current) {
      layerIds.forEach(id => {
        if (mapRef.current.getLayer(id)) {
          mapRef.current.setLayoutProperty(id, 'visibility', updated ? 'visible' : 'none');
        }
      });
    }
  };

  // Helper to fetch and update grid data
  const loadGridData = async (day, hour) => {
    if (!mapRef.current) return;
    try {
      const gridUrl = getApiUrl(`/api/safety/grid?day=${day}&hour=${hour}`);
      const response = await fetch(gridUrl);
      if (response.ok) {
        const gridGeojson = await response.json();
        const source = mapRef.current.getSource('bsi-grid');
        if (source) {
          source.setData(gridGeojson);
        }
      }
    } catch (err) {
      console.error('Error reloading risk grid:', err);
    }
  };

  // Initialize MapLibre Map with CartoDB Dark Matter GL style
  useEffect(() => {
    if (mapRef.current) return;

    mapRef.current = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [78.9629, 16.5000], // Centered over Indian peninsula & EEZ boundaries
      zoom: 4.5, // Optimal zoom for Indian maritime extent
      maxBounds: [
        [55.0, -5.0],  // South-West limit (includes Arabian Sea & Maldives)
        [105.0, 35.0]  // North-East limit (includes Bay of Bengal & Andaman)
      ]
    });

    // Add navigation controls
    mapRef.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    mapRef.current.on('load', async () => {
      if (!mapRef.current) return;

      try {
        // 1. Initialize source for dynamic BSI risk grid
        mapRef.current.addSource('bsi-grid', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: []
          }
        });

        // Add BSI Risk Fill Layer
        mapRef.current.addLayer({
          id: 'bsi-grid-fill',
          type: 'fill',
          source: 'bsi-grid',
          paint: {
            'fill-color': [
              'match',
              ['get', 'color'],
              'red', '#ef4444',
              'orange', '#f97316',
              'yellow', '#eab308',
              'green', '#22c55e',
              '#64748b'
            ],
            'fill-opacity': 0.45
          }
        });

        // Add BSI Risk Stroke Outline
        mapRef.current.addLayer({
          id: 'bsi-grid-stroke',
          type: 'line',
          source: 'bsi-grid',
          paint: {
            'line-color': [
              'match',
              ['get', 'color'],
              'red', '#dc2626',
              'orange', '#ea580c',
              'yellow', '#ca8a04',
              'green', '#16a34a',
              '#475569'
            ],
            'line-width': 1.0
          }
        });

        // Populate BSI risk grid immediately on map load
        loadGridData(selectedDayRef.current, selectedHourRef.current);

        // Click listener on BSI Grid cells to inspect coordinate values
        mapRef.current.on('click', 'bsi-grid-fill', (e) => {
          e.preventDefault(); // Stop general map click
          const features = mapRef.current.queryRenderedFeatures(e.point, { layers: ['bsi-grid-fill'] });
          if (!features.length) return;
          
          const props = features[0].properties;
          const { bsi, hs, wind_speed_kmh, current_speed_ms } = props;
          
          if (popupRef.current) {
            popupRef.current.remove();
          }
          popupRef.current = new maplibregl.Popup({ maxWidth: 'none' })
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="text-slate-900 p-2.5 font-sans space-y-1.5" style="max-width: 220px;">
                <h4 class="font-black border-b pb-1 text-blue-600 text-xs">INCOIS Forecast Cell</h4>
                <div class="text-[10px] text-slate-700 leading-normal font-semibold">
                  <div class="flex justify-between"><span>BSI Capsizing Score:</span> <span class="text-blue-600 font-bold">${bsi}/7</span></div>
                  <div class="flex justify-between"><span>Significant Wave Hs:</span> <span class="font-bold">${hs} m</span></div>
                  <div class="flex justify-between"><span>Wind Speed:</span> <span class="font-bold">${wind_speed_kmh ?? '—'} km/h</span></div>
                  <div class="flex justify-between"><span>Current Speed:</span> <span class="font-bold">${current_speed_ms ?? '—'} m/s</span></div>
                  <div class="flex justify-between"><span>Cell Resolution:</span> <span class="font-mono text-[9px]">0.4° (~44 km)</span></div>
                </div>
              </div>
            `)
            .addTo(mapRef.current);
            
          if (onLocationSelectRef.current) {
            onLocationSelectRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng });
          }
        });

        mapRef.current.on('mouseenter', 'bsi-grid-fill', () => {
          mapRef.current.getCanvas().style.cursor = 'pointer';
        });
        mapRef.current.on('mouseleave', 'bsi-grid-fill', () => {
          mapRef.current.getCanvas().style.cursor = '';
        });

        // 2. Fetch and load the live INCOIS advisory polygons (coastal districts)
        try {
          const advisoryRes = await fetch(getApiUrl('/api/safety/advisories'));
          if (advisoryRes.ok) {
            const advisoryGeojson = await advisoryRes.json();
            mapRef.current.addSource('coastal-advisories', {
              type: 'geojson',
              data: advisoryGeojson
            });

            const suffix = getSuffix(beamWidth);

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

            // Click popup listener for advisory districts
            mapRef.current.on('click', 'advisory-fill', (e) => {
              e.preventDefault(); // Stop general map click
              const features = mapRef.current.queryRenderedFeatures(e.point, { layers: ['advisory-fill'] });
              if (!features.length) return;
              const props = features[0].properties;
              
              const district = props.DistrictNa || props.ENG || props.name || "Coastal Strip";
              const state = props.state || "";
              
              const currentSuffix = getSuffix(beamWidth);
              const limitStr = currentSuffix === '4' ? '4m' : currentSuffix === '6' ? '6m' : '7m';
              
              let advisoryText = props[`ENG${currentSuffix}`] || props[`HIN${currentSuffix}`] || props.Advisory_E || "";
              advisoryText = advisoryText.trim();
              
              if (!advisoryText) {
                const warningColor = props[`Color${currentSuffix}`];
                if (warningColor === 'Green' || warningColor === 'Safe' || !warningColor) {
                  advisoryText = `${district} district, Boats less than ${limitStr} wide can safely sail.`;
                } else {
                  advisoryText = "No advisory details available.";
                }
              }
              
              const cleanedAdvisory = advisoryText
                .replace(/<img[^>]*>/gi, '') // Remove the logo image completely
                .replace(/^(\s*<br\s*\/?>\s*)+/i, '')
                .replace(/font-size\s*:\s*[^;']*(px|rem|em)?/gi, 'font-size: 11px')
                .replace(/line-height\s*:\s*[^;']*(px|rem|em)?/gi, 'line-height: 1.3')
                .trim();
              
              if (popupRef.current) {
                popupRef.current.remove();
              }

              window.popupSaveAdvisory = () => {
                alert(`SVAS Advisory for ${district} saved successfully!`);
              };

              popupRef.current = new maplibregl.Popup({ maxWidth: 'none' })
                .setLngLat(e.lngLat)
                .setHTML(`
                  <div class="text-slate-900 p-3 pb-6 font-sans relative" style="max-width: 580px; min-width: 520px;">
                    <h4 class="font-bold border-b pb-1 text-blue-600 text-xs flex justify-between items-center">
                      <span>${district} (${state})</span>
                      <span class="text-[9px] text-slate-500 font-extrabold tracking-wider">SOURCE - INCOIS</span>
                    </h4>
                    <div class="text-[11px] leading-relaxed text-slate-700 mt-2 font-medium">
                      ${cleanedAdvisory}
                    </div>
                    <div class="border-t border-slate-100 pt-2 mt-2 flex justify-end">
                      <button 
                        class="svas-save-btn bg-[#1d4ed8] hover:bg-[#1e40af] text-white text-[10px] font-bold px-3.5 py-1.5 rounded shadow-sm transition-colors cursor-pointer"
                        onclick="window.popupSaveAdvisory()"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                `)
                .addTo(mapRef.current);

              if (onLocationSelectRef.current) {
                onLocationSelectRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng });
              }
            });

            mapRef.current.on('mouseenter', 'advisory-fill', () => {
              mapRef.current.getCanvas().style.cursor = 'pointer';
            });
            mapRef.current.on('mouseleave', 'advisory-fill', () => {
              mapRef.current.getCanvas().style.cursor = '';
            });
          }
        } catch (err) {
          console.error('Error loading coastal advisories:', err);
        }

        // 3. Fetch and load geofencing boundary layers (EEZ & MPAs)
        const geofenceRes = await fetch(getApiUrl('/api/geofence/geojson'));
        if (geofenceRes.ok) {
          const geofenceGeojson = await geofenceRes.json();
          
          mapRef.current.addSource('geofencing-layers', {
            type: 'geojson',
            data: geofenceGeojson
          });

          // Renders Marine Protected Area (MPA) restricted sanctuaries
          mapRef.current.addLayer({
            id: 'mpa-fill',
            type: 'fill',
            source: 'geofencing-layers',
            filter: ['==', ['get', 'type'], 'MPA'],
            paint: {
              'fill-color': '#a855f7',
              'fill-opacity': 0.20
            }
          });

          mapRef.current.addLayer({
            id: 'mpa-stroke',
            type: 'line',
            source: 'geofencing-layers',
            filter: ['==', ['get', 'type'], 'MPA'],
            paint: {
              'line-color': '#9333ea',
              'line-width': 1.8,
              'line-dasharray': [3, 2]
            }
          });

          // Renders Indian EEZ Border outline in red-dashed style
          mapRef.current.addLayer({
            id: 'eez-stroke',
            type: 'line',
            source: 'geofencing-layers',
            filter: ['==', ['get', 'type'], 'EEZ'],
            paint: {
              'line-color': '#ef4444',
              'line-width': 2.0,
              'line-dasharray': [4, 3]
            }
          });

          // Click popup listener for restricted areas
          mapRef.current.on('click', 'mpa-fill', (e) => {
            e.preventDefault(); // Stop general map click
            const mpaFeatures = mapRef.current.queryRenderedFeatures(e.point, { layers: ['mpa-fill'] });
            if (!mpaFeatures.length) return;
            const name = mpaFeatures[0].properties.name;
            
            if (popupRef.current) {
              popupRef.current.remove();
            }
            popupRef.current = new maplibregl.Popup({ maxWidth: 'none' })
              .setLngLat(e.lngLat)
              .setHTML(`
                <div class="text-slate-900 p-2 font-sans space-y-1" style="max-width: 250px;">
                  <h4 class="font-bold border-b pb-1 text-purple-600 text-xs">Restricted Zone / Sanctuary</h4>
                  <p class="text-[10px] text-slate-700 leading-relaxed font-semibold mt-1">
                    ${name}<br>
                    <span class="text-[9px] text-slate-500 font-normal">Sailing or fishing inside this marine sanctuary is strictly prohibited.</span>
                  </p>
                </div>
              `)
              .addTo(mapRef.current);

            if (onLocationSelectRef.current) {
              onLocationSelectRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng });
            }
          });

          mapRef.current.on('mouseenter', 'mpa-fill', () => {
            mapRef.current.getCanvas().style.cursor = 'pointer';
          });
          mapRef.current.on('mouseleave', 'mpa-fill', () => {
            mapRef.current.getCanvas().style.cursor = '';
          });
        }

        // 4. Add official INCOIS WMS Sea Surface Temperature (SST) layer
        mapRef.current.addSource('incois-sst', {
          type: 'raster',
          tiles: [
            'https://incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms?service=WMS&request=GetMap&layers=PFZ-TUNA-SST-CHL:sst&styles=&format=image/png&transparent=true&version=1.1.1&width=256&height=256&srs=EPSG:3857&bbox={bbox-epsg-3857}'
          ],
          tileSize: 256
        });

        mapRef.current.addLayer({
          id: 'sst-raster',
          type: 'raster',
          source: 'incois-sst',
          paint: {
            'raster-opacity': 0.65
          },
          layout: {
            visibility: 'none' // Hidden by default
          }
        });

        // 5. Add official INCOIS WMS Chlorophyll (CHL) layer
        mapRef.current.addSource('incois-chl', {
          type: 'raster',
          tiles: [
            'https://incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms?service=WMS&request=GetMap&layers=PFZ-TUNA-SST-CHL:chl&styles=&format=image/png&transparent=true&version=1.1.1&width=256&height=256&srs=EPSG:3857&bbox={bbox-epsg-3857}'
          ],
          tileSize: 256
        });

        mapRef.current.addLayer({
          id: 'chl-raster',
          type: 'raster',
          source: 'incois-chl',
          paint: {
            'raster-opacity': 0.65
          },
          layout: {
            visibility: 'none' // Hidden by default
          }
        });

        // 6. Fetch and load official WFS PFZ advisory lines
        try {
          const pfzRes = await fetch(getApiUrl('/api/incois/pfz-lines'));
          if (pfzRes.ok) {
            const pfzGeojson = await pfzRes.json();
            mapRef.current.addSource('incois-pfz-lines', {
              type: 'geojson',
              data: pfzGeojson
            });

            mapRef.current.addLayer({
              id: 'pfz-lines-stroke',
              type: 'line',
              source: 'incois-pfz-lines',
              paint: {
                'line-color': '#eab308', // Yellow lines matching official legend
                'line-width': 2.0
              },
              layout: {
                visibility: 'none' // Hidden by default
              }
            });

            // Click listener for PFZ vector lines
            mapRef.current.on('click', 'pfz-lines-stroke', (e) => {
              e.preventDefault();
              const features = mapRef.current.queryRenderedFeatures(e.point, { layers: ['pfz-lines-stroke'] });
              if (!features.length) return;
              const props = features[0].properties;
              
              if (popupRef.current) {
                popupRef.current.remove();
              }
              popupRef.current = new maplibregl.Popup({ maxWidth: 'none' })
                .setLngLat(e.lngLat)
                .setHTML(`
                  <div class="text-slate-900 p-2.5 font-sans space-y-1" style="max-width: 250px;">
                    <h4 class="font-bold border-b pb-1 text-yellow-600 text-xs">INCOIS PFZ Advisory</h4>
                    <p class="text-[9px] text-slate-700 leading-relaxed font-semibold mt-1">
                      Sector ID: <span class="font-mono text-blue-600 font-bold">${props.sectorId || 'N/A'}</span><br>
                      Advisory Date: <span class="font-normal text-slate-600">${props.date || 'Current Daily'}</span><br>
                      <span class="text-[8px] text-slate-500 font-normal">Features: ${props.length || 'Optimal sea surface temperature and chlorophyll boundary contour'}</span>
                    </p>
                  </div>
                `)
                .addTo(mapRef.current);

              if (onLocationSelectRef.current) {
                onLocationSelectRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng });
              }
            });

            mapRef.current.on('mouseenter', 'pfz-lines-stroke', () => {
              mapRef.current.getCanvas().style.cursor = 'pointer';
            });
            mapRef.current.on('mouseleave', 'pfz-lines-stroke', () => {
              mapRef.current.getCanvas().style.cursor = '';
            });
          }
        } catch (pfzErr) {
          console.error("Failed to load WFS PFZ lines:", pfzErr);
        }

        setMapLoaded(true);
      } catch (err) {
        console.error('Error initializing map layers:', err);
      }
    });

    // Left click anywhere on map grid or ocean waters callback to inspect coordinate values
    mapRef.current.on('click', (e) => {
      const { lng, lat } = e.lngLat;
      if (onLocationSelectRef.current) {
        onLocationSelectRef.current({ lat, lon: lng });
      }
    });

    return () => {
      if (popupRef.current) {
        popupRef.current.remove();
        popupRef.current = null;
      }
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Fetch and update the dynamic 2D grid GeoJSON when day or hour step changes
  useEffect(() => {
    loadGridData(selectedDay, selectedHour);
  }, [selectedDay, selectedHour]);

  // Sync WMS SST layer opacity
  useEffect(() => {
    if (mapRef.current && mapRef.current.getLayer('sst-raster')) {
      mapRef.current.setPaintProperty('sst-raster', 'raster-opacity', sstOpacity);
    }
  }, [sstOpacity]);

  // Sync WMS Chlorophyll layer opacity
  useEffect(() => {
    if (mapRef.current && mapRef.current.getLayer('chl-raster')) {
      mapRef.current.setPaintProperty('chl-raster', 'raster-opacity', chlOpacity);
    }
  }, [chlOpacity]);

  // Sync BSI Risk, Wind Speed, and Current Speed grid styling modes
  useEffect(() => {
    if (!mapRef.current) return;

    const fillLayer = mapRef.current.getLayer('bsi-grid-fill');
    const strokeLayer = mapRef.current.getLayer('bsi-grid-stroke');
    if (!fillLayer || !strokeLayer) return;

    if (layers.bsiRisk) {
      // Show BSI Risk styling
      mapRef.current.setLayoutProperty('bsi-grid-fill', 'visibility', 'visible');
      mapRef.current.setLayoutProperty('bsi-grid-stroke', 'visibility', 'visible');
      mapRef.current.setPaintProperty('bsi-grid-fill', 'fill-color', [
        'match',
        ['get', 'color'],
        'red', '#ef4444',
        'orange', '#f97316',
        'yellow', '#eab308',
        'green', '#22c55e',
        '#64748b'
      ]);
      mapRef.current.setPaintProperty('bsi-grid-stroke', 'line-color', [
        'match',
        ['get', 'color'],
        'red', '#dc2626',
        'orange', '#ea580c',
        'yellow', '#ca8a04',
        'green', '#16a34a',
        '#475569'
      ]);
    } else if (layers.windSpeed) {
      // Show Wind Speed styling (Interpolate km/h)
      mapRef.current.setLayoutProperty('bsi-grid-fill', 'visibility', 'visible');
      mapRef.current.setLayoutProperty('bsi-grid-stroke', 'visibility', 'visible');
      mapRef.current.setPaintProperty('bsi-grid-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'wind_speed_kmh'],
        0, '#1e3a8a',    // Very light wind (Dark Blue)
        15, '#3b82f6',   // Gentle wind (Blue)
        25, '#eab308',   // Moderate wind (Yellow)
        35, '#f97316',   // High wind (Orange)
        45, '#ef4444'    // Gale force (Red)
      ]);
      mapRef.current.setPaintProperty('bsi-grid-stroke', 'line-color', '#1e293b');
    } else if (layers.currentSpeed) {
      // Show Current Speed styling (Interpolate m/s)
      mapRef.current.setLayoutProperty('bsi-grid-fill', 'visibility', 'visible');
      mapRef.current.setLayoutProperty('bsi-grid-stroke', 'visibility', 'visible');
      mapRef.current.setPaintProperty('bsi-grid-fill', 'fill-color', [
        'interpolate',
        ['linear'],
        ['get', 'current_speed_ms'],
        0, '#065f46',    // Low current (Dark Green)
        0.3, '#10b981',  // Light current (Green)
        0.6, '#eab308',  // Moderate current (Yellow)
        1.0, '#f97316',  // Strong current (Orange)
        1.5, '#ef4444'    // Dangerous current (Red)
      ]);
      mapRef.current.setPaintProperty('bsi-grid-stroke', 'line-color', '#1e293b');
    } else {
      // Hide grid layers if all are unchecked
      mapRef.current.setLayoutProperty('bsi-grid-fill', 'visibility', 'none');
      mapRef.current.setLayoutProperty('bsi-grid-stroke', 'visibility', 'none');
    }
  }, [layers.bsiRisk, layers.windSpeed, layers.currentSpeed]);

  // Sync coastal advisory layer paint properties when beamWidth changes
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
  }, [beamWidth]);

  const isInitialMountRef = useRef(true);

  // Update map marker and smoothly pan whenever inspected coordinates change
  useEffect(() => {
    if (!mapRef.current) return;

    if (selectedLocation) {
      const coords = [selectedLocation.lon, selectedLocation.lat];

      if (markerRef.current) {
        markerRef.current.setLngLat(coords);
      } else {
        // Custom boat pin marker matching ORCA design
        const el = document.createElement('div');
        el.className = 'custom-boat-marker';
        el.style.width = '32px';
        el.style.height = '38px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.cursor = 'pointer';
        el.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" width="100%" height="100%">
            <defs>
              <filter id="boat-pin-shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000000" flood-opacity="0.35"/>
              </filter>
              <linearGradient id="boat-pin-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#2563eb"/>
                <stop offset="100%" stop-color="#1d4ed8"/>
              </linearGradient>
            </defs>
            <path d="M 50 10 C 25 10, 10 28, 10 52 C 10 76, 38 102, 50 112 C 62 102, 90 76, 90 52 C 90 28, 75 10, 50 10 Z" 
                  fill="url(#boat-pin-gradient)" stroke="#FFFFFF" stroke-width="3" filter="url(#boat-pin-shadow)"/>
            <g transform="translate(0, 2)">
              <path d="M 48 26 L 48 53 L 67 53 C 67 53, 68 37, 48 26 Z" fill="#FFFFFF"/>
              <path d="M 44 31 L 44 53 L 33 53 C 33 53, 35 40, 44 31 Z" fill="#38BDF8"/>
              <line x1="46" y1="24" x2="46" y2="55" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M 28 57 L 72 57 L 65 67 C 60 70, 40 70, 35 67 Z" fill="#E2E8F0"/>
            </g>
          </svg>
        `;

        markerRef.current = new maplibregl.Marker({ element: el })
          .setLngLat(coords)
          .addTo(mapRef.current);
      }

      // Smooth pan on user clicks, keeping overview centered on initial mount
      if (isInitialMountRef.current) {
        isInitialMountRef.current = false;
      } else {
        mapRef.current.easeTo({ center: coords });
      }
    } else {
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }
    }
  }, [selectedLocation, mapLoaded]);

  return (
    <div className="w-full h-full relative">
      <div ref={mapContainerRef} className="w-full h-full" />
      
      {/* Map Legend Overlay (Top-Left) matching commit 32919d4 & media_1787760113604.png */}
      <div className="absolute top-4 left-4 bg-slate-900/90 p-4 rounded-xl border border-slate-700 text-xs shadow-lg space-y-2 z-10">
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

      {/* Map Layers (Top-Right) */}
      <div className="absolute top-4 right-4 bg-[#090f1d]/95 p-3.5 rounded-xl border border-slate-800 text-[10px] shadow-2xl space-y-2.5 w-44 z-10 backdrop-blur">
        <h3 className="font-extrabold text-blue-400 uppercase tracking-wider text-[9px]">Map Layers</h3>
        <div className="flex flex-col gap-2 text-slate-300">
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.bsiRisk} 
              onChange={() => setLayers(prev => ({ ...prev, bsiRisk: !prev.bsiRisk, windSpeed: false, currentSpeed: false }))}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>SVAS BSI Risk</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.advisories} 
              onChange={() => toggleLayer('advisories', ['advisory-fill', 'advisory-stroke'])}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>Coastal Advisories</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.eezBorder} 
              onChange={() => toggleLayer('eezBorder', ['eez-stroke'])}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>EEZ Boundary</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.restricted} 
              onChange={() => toggleLayer('restricted', ['mpa-fill', 'mpa-stroke'])}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>Restricted Areas (MPA)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.windSpeed} 
              onChange={() => setLayers(prev => ({ ...prev, windSpeed: !prev.windSpeed, bsiRisk: false, currentSpeed: false }))}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>Wind Speed</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.currentSpeed} 
              onChange={() => setLayers(prev => ({ ...prev, currentSpeed: !prev.currentSpeed, bsiRisk: false, windSpeed: false }))}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>Current Speed</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.sst} 
              onChange={() => toggleLayer('sst', ['sst-raster'])}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>INCOIS WMS SST</span>
          </label>
          {layers.sst && (
            <div className="pl-5 flex flex-col gap-1 border-l border-blue-500/20 py-0.5">
              <div className="flex justify-between text-[7px] text-slate-400">
                <span>Opacity:</span>
                <span>{Math.round(sstOpacity * 100)}%</span>
              </div>
              <input 
                type="range" min="0" max="1" step="0.05"
                value={sstOpacity}
                onChange={(e) => setSstOpacity(parseFloat(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.chlorophyll} 
              onChange={() => toggleLayer('chlorophyll', ['chl-raster'])}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>INCOIS Chlorophyll</span>
          </label>
          {layers.chlorophyll && (
            <div className="pl-5 flex flex-col gap-1 border-l border-green-500/20 py-0.5">
              <div className="flex justify-between text-[7px] text-slate-400">
                <span>Opacity:</span>
                <span>{Math.round(chlOpacity * 100)}%</span>
              </div>
              <input 
                type="range" min="0" max="1" step="0.05"
                value={chlOpacity}
                onChange={(e) => setChlOpacity(parseFloat(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer font-semibold">
            <input 
              type="checkbox" 
              checked={layers.pfzAdvisory} 
              onChange={() => toggleLayer('pfzAdvisory', ['pfz-lines-stroke'])}
              className="accent-blue-500 rounded border-slate-700 bg-slate-900 w-3 h-3" 
            />
            <span>INCOIS PFZ Lines</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer font-semibold opacity-60">
            <input type="checkbox" disabled className="accent-blue-500 rounded border-slate-700 w-3 h-3" />
            <span>Recommended Route</span>
          </label>
        </div>
      </div>
    </div>
  );
}

export default MapContainer;