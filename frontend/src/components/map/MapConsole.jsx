import React, { useEffect, useRef, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import MapLegend from './MapLegend';
import { getPointAnalytics } from '../../services/api';

const getApiUrl = (path) => {
  if (typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location;
    if (protocol === 'file:' || ((hostname === 'localhost' || hostname === '127.0.0.1') && port !== '8000')) {
      return `http://127.0.0.1:8000${path}`;
    }
  }
  return path;
};

const getSuffix = (width) => {
  if (width < 4.0) return '4';
  if (width < 6.0) return '6';
  return '7';
};

const EMPTY_FEATURE_COLLECTION = {
  type: 'FeatureCollection',
  features: []
};

/**
 * MapConsole - WebGL MapLibre GL Map Engine for Naval Operations Console.
 * Single persistent map instance with dynamic mode-based layer visibility toggling.
 */
export function MapConsole({
  activeMode = 'routing',
  selectedLocation = null,
  onLocationSelect,
  destinationLocation = null,
  onDestinationSelect,
  routeData = null,
  pfzGeojson = null,
  advisoriesGeojson = null,
  geofenceGeojson = null,
  gridGeojson = null,
  vectorGrid = { windGeojson: null, currentGeojson: null },
  sstOpacity = 0.65,
  chlOpacity = 0.65,
  beamWidth = 3.5,
  layersOverride = {},
  onPfzInspect,
  selectedNodeId,
  onNodeSelect,
  className = ''
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const boatMarkerRef = useRef(null);
  const destMarkerRef = useRef(null);
  const popupRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const isInitialMountRef = useRef(true);

  // Keep callback refs fresh to avoid stale closures in MapLibre event listeners
  const onLocationSelectRef = useRef(onLocationSelect);
  const onDestinationSelectRef = useRef(onDestinationSelect);
  const onPfzInspectRef = useRef(onPfzInspect);
  const activeModeRef = useRef(activeMode);
  const beamWidthRef = useRef(beamWidth);
  const layersOverrideRef = useRef(layersOverride);
  const selectedLocationRef = useRef(selectedLocation);

  useEffect(() => { onLocationSelectRef.current = onLocationSelect; }, [onLocationSelect]);
  useEffect(() => { onDestinationSelectRef.current = onDestinationSelect; }, [onDestinationSelect]);
  useEffect(() => { onPfzInspectRef.current = onPfzInspect; }, [onPfzInspect]);
  useEffect(() => { activeModeRef.current = activeMode; }, [activeMode]);
  useEffect(() => { beamWidthRef.current = beamWidth; }, [beamWidth]);
  useEffect(() => { layersOverrideRef.current = layersOverride; }, [layersOverride]);
  useEffect(() => { selectedLocationRef.current = selectedLocation; }, [selectedLocation]);

  // Helper to safely set GeoJSON data on a source if present
  const setSourceDataSafe = useCallback((sourceId, data) => {
    if (!mapRef.current) return;
    const source = mapRef.current.getSource(sourceId);
    if (source && typeof source.setData === 'function') {
      source.setData(data || EMPTY_FEATURE_COLLECTION);
    }
  }, []);

  // 1. Map Initialization (mounted ONCE)
  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [78.9629, 16.5000], // Centered over Indian peninsula & EEZ boundaries
      zoom: 4.5,
      maxBounds: [
        [55.0, -5.0],  // South-West limit (Arabian Sea & Maldives)
        [105.0, 35.0]  // North-East limit (Bay of Bengal & Andaman)
      ]
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    mapRef.current = map;

    map.on('load', async () => {
      // 0. Load Arrow Icon for Vector Grids
      const arrowSvg = `
        <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2 L20 20 L12 16 L4 20 Z" fill="black" />
        </svg>
      `;
      const img = new Image(24, 24);
      img.onload = () => {
        if (!map.hasImage('arrow-icon')) {
          map.addImage('arrow-icon', img, { sdf: true });
        }
      };
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(arrowSvg);
      if (!mapRef.current) return;

      try {
        // --- 1. Source: bsi-grid (Invisible Interaction Layer) ---
        map.addSource('bsi-grid', {
          type: 'geojson',
          data: gridGeojson || EMPTY_FEATURE_COLLECTION
        });

        // Layer 1: bsi-grid-fill (Invisible but clickable)
        map.addLayer({
          id: 'bsi-grid-fill',
          type: 'fill',
          source: 'bsi-grid',
          paint: {
            'fill-opacity': 0.0 // Completely invisible, used only for onClick events
          },
          layout: { visibility: 'none' }
        });

        // --- 1.5. Source: bsi-points (For Smooth Heatmap) ---
        map.addSource('bsi-points', {
          type: 'geojson',
          data: EMPTY_FEATURE_COLLECTION
        });

        // Layer 2: bsi-heatmap (Data-driven blurred circles)
        map.addLayer({
          id: 'bsi-heatmap',
          type: 'circle',
          source: 'bsi-points',
          paint: {
            'circle-color': [
              'interpolate',
              ['linear'],
              ['get', 'severity'],
              0, '#18C7A0',  // Safe (Green)
              40, '#18C7A0', // Stay green longer
              50, '#FFB547', // Moderate (Yellow)
              70, '#FF5C5C', // High (Red)
              100, '#FF5C5C' // Extreme (Red)
            ],
            // Scale radius up as you zoom in to keep the screen covered in color
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 0, 15, 6, 25, 10, 60],
            // Apply maximum blur so individual circles completely blend together
            'circle-blur': 1.0,
            'circle-opacity': 0.65,
            'circle-stroke-width': 0
          },
          layout: { visibility: 'visible' }
        });

        // --- 3. Source: geofencing-layers ---
        map.addSource('geofencing-layers', {
          type: 'geojson',
          data: geofenceGeojson || EMPTY_FEATURE_COLLECTION
        });

        // Layer 5: mpa-fill (Restricted Sanctuaries)
        map.addLayer({
          id: 'mpa-fill',
          type: 'fill',
          source: 'geofencing-layers',
          filter: ['==', ['get', 'type'], 'MPA'],
          paint: {
            'fill-color': '#a855f7',
            'fill-opacity': 0.20
          },
          layout: { visibility: 'visible' }
        });

        // Layer 6: mpa-stroke
        map.addLayer({
          id: 'mpa-stroke',
          type: 'line',
          source: 'geofencing-layers',
          filter: ['==', ['get', 'type'], 'MPA'],
          paint: {
            'line-color': '#9333ea',
            'line-width': 1.8,
            'line-dasharray': [3, 2]
          },
          layout: { visibility: 'visible' }
        });

        // Layer 7: eez-stroke (Indian EEZ Border)
        map.addLayer({
          id: 'eez-stroke',
          type: 'line',
          source: 'geofencing-layers',
          filter: ['==', ['get', 'type'], 'EEZ'],
          paint: {
            'line-color': '#FF5C5C',
            'line-width': 2.0,
            'line-dasharray': [4, 3]
          },
          layout: { visibility: 'visible' }
        });

        // --- 4. Source: incois-sst (Raster WMS) ---
        map.addSource('incois-sst', {
          type: 'raster',
          tiles: [
            getApiUrl('/api/incois/wms/proxy?layers=PFZ-TUNA-SST-CHL:sst&bbox={bbox-epsg-3857}')
          ],
          tileSize: 256
        });

        // Layer 8: sst-raster
        map.addLayer({
          id: 'sst-raster',
          type: 'raster',
          source: 'incois-sst',
          paint: {
            'raster-opacity': sstOpacity
          },
          layout: { visibility: 'none' }
        });

        // --- 5. Source: incois-chl (Raster WMS) ---
        map.addSource('incois-chl', {
          type: 'raster',
          tiles: [
            getApiUrl('/api/incois/wms/proxy?layers=PFZ-TUNA-SST-CHL:chl&bbox={bbox-epsg-3857}')
          ],
          tileSize: 256
        });

        // Layer 9: chl-raster
        map.addLayer({
          id: 'chl-raster',
          type: 'raster',
          source: 'incois-chl',
          paint: {
            'raster-opacity': chlOpacity
          },
          layout: { visibility: 'none' }
        });

        // --- 6. Source: vector-wind ---
        map.addSource('vector-wind', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });

        // Layer 10: wind-arrows
        map.addLayer({
          id: 'wind-arrows',
          type: 'symbol',
          source: 'vector-wind',
          layout: {
            'icon-image': 'arrow-icon',
            'icon-rotate': ['get', 'direction_deg'],
            'icon-rotation-alignment': 'map',
            'icon-allow-overlap': false,
            'icon-size': [
              'interpolate', ['linear'], ['zoom'],
              3, 0.2,
              6, 0.6,
              9, 1.0
            ],
            'icon-padding': 2,
            visibility: 'none'
          },
          paint: {
            'icon-color': [
              'interpolate', ['linear'], ['get', 'speed_kmh'],
              0, '#00D4FF',
              20, '#18C7A0',
              40, '#FFB547',
              60, '#FF5C5C'
            ],
            'icon-halo-color': '#07111F',
            'icon-halo-width': 1
          }
        });

        // --- 7. Source: vector-current ---
        map.addSource('vector-current', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });

        // Layer 11: current-arrows
        map.addLayer({
          id: 'current-arrows',
          type: 'symbol',
          source: 'vector-current',
          layout: {
            'icon-image': 'arrow-icon',
            'icon-rotate': ['get', 'direction_deg'],
            'icon-rotation-alignment': 'map',
            'icon-allow-overlap': false,
            'icon-size': [
              'interpolate', ['linear'], ['zoom'],
              3, 0.2,
              6, 0.6,
              9, 1.0
            ],
            'icon-padding': 2,
            visibility: 'none'
          },
          paint: {
            'icon-color': [
              'interpolate', ['linear'], ['get', 'speed_ms'],
              0, '#00D4FF',
              0.5, '#18C7A0',
              1.0, '#FFB547',
              1.5, '#FF5C5C'
            ],
            'icon-halo-color': '#07111F',
            'icon-halo-width': 1
          }
        });


        const routeCoords = routeData?.path?.map(n => [n.lon, n.lat]) || [];
        const straightCoords = routeCoords.length > 0 ? [routeCoords[0], routeCoords[routeCoords.length - 1]] : [];

        // --- 6. Source: optimized-route (A* Path Vector) ---
        map.addSource('optimized-route', {
          type: 'geojson',
          data: routeCoords.length ? {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: routeCoords }
          } : EMPTY_FEATURE_COLLECTION
        });

        // Layer 10: route-line (Cyan accent in Navik)
        map.addLayer({
          id: 'route-line',
          type: 'line',
          source: 'optimized-route',
          paint: {
            'line-color': '#00D4FF',
            'line-width': 4.0
          },
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
            visibility: 'none'
          }
        });

        // --- 7. Source: straight-route (Direct Baseline Comparison) ---
        map.addSource('straight-route', {
          type: 'geojson',
          data: straightCoords.length ? {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: straightCoords }
          } : EMPTY_FEATURE_COLLECTION
        });

        // Layer 11: straight-line
        map.addLayer({
          id: 'straight-line',
          type: 'line',
          source: 'straight-route',
          paint: {
            'line-color': '#8FA8B8',
            'line-width': 1.5,
            'line-dasharray': [3, 3]
          },
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
            visibility: 'none'
          }
        });

        // --- Route Nodes for Interaction ---
        map.addSource('route-nodes', {
          type: 'geojson',
          data: EMPTY_FEATURE_COLLECTION
        });
        
        map.addLayer({
          id: 'route-nodes-layer',
          type: 'circle',
          source: 'route-nodes',
          paint: {
            'circle-radius': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              8,
              5
            ],
            'circle-color': ['get', 'color'],
            'circle-stroke-width': [
              'case',
              ['boolean', ['feature-state', 'selected'], false],
              2,
              1
            ],
            'circle-stroke-color': '#EAF4F8'
          },
          layout: { visibility: 'none' }
        });


        // --- 8. Source: incois-pfz-lines (WFS PFZ Advisory Vectors) ---
        map.addSource('incois-pfz-lines', {
          type: 'geojson',
          data: pfzGeojson || EMPTY_FEATURE_COLLECTION
        });

        // Layer 12: pfz-lines-stroke
        map.addLayer({
          id: 'pfz-lines-stroke',
          type: 'line',
          source: 'incois-pfz-lines',
          paint: {
            'line-color': '#FFB547',
            'line-width': 2.5
          },
          layout: { visibility: 'none' }
        });

        // --- 9. Source: coastal-advisories (SVAS Polygons) ---
        map.addSource('coastal-advisories', {
          type: 'geojson',
          data: advisoriesGeojson || EMPTY_FEATURE_COLLECTION
        });

        const initialSuffix = getSuffix(beamWidthRef.current || 3.5);
        map.addLayer({
          id: 'advisory-fill',
          type: 'fill',
          source: 'coastal-advisories',
          paint: {
            'fill-opacity': 0.65,
            'fill-color': [
              'case',
              ['==', ['get', `Color${initialSuffix}`], 'orange'], '#FFB547',
              ['==', ['get', `Color${initialSuffix}`], 'red'], '#FF5C5C',
              '#18C7A0'
            ]
          },
          layout: { visibility: 'visible' }
        });

        map.addLayer({
          id: 'advisory-stroke',
          type: 'line',
          source: 'coastal-advisories',
          paint: {
            'line-color': [
              'case',
              ['==', ['get', `Color${initialSuffix}`], 'orange'], '#FB923C',
              ['==', ['get', `Color${initialSuffix}`], 'red'], '#F87171',
              '#4ADE80'
            ],
            'line-width': 1.5,
            'line-opacity': 0.8
          },
          layout: { visibility: 'visible' }
        });


        // Interactive Popups & Event Handlers
        // -------------------------------------------------------------

        // Helper for Universal Ocean Point Telemetry Popup (Requirement R4)
        const handleOceanPointClick = (lngLat) => {
          const clickLat = lngLat.lat;
          const clickLon = lngLat.lng;

          if (popupRef.current) {
            popupRef.current.remove();
            popupRef.current = null;
          }

          const popupDom = document.createElement('div');
          popupDom.className = 'bg-[#0D1B2A] text-[#EAF4F8] p-3.5 rounded-xl border border-[#00D4FF]/40 font-sans shadow-2xl space-y-2.5';
          popupDom.style.maxWidth = '300px';
          popupDom.innerHTML = `
            <div class="flex items-center justify-between border-b border-[#20384D] pb-1.5">
              <span class="font-mono text-xs font-bold text-[#00D4FF]">INCOIS Point Telemetry</span>
              <span class="font-mono text-[9px] text-[#18C7A0] font-bold uppercase animate-pulse">SAMPLING...</span>
            </div>
            <div class="text-[10px] text-[#8FA8B8] font-mono space-y-1">
              <div>Coordinates: <span class="text-[#EAF4F8] font-bold">${clickLat.toFixed(4)}°N, ${clickLon.toFixed(4)}°E</span></div>
              <div class="text-[9px] text-[#8FA8B8] italic">Querying oceanographic telemetry...</div>
            </div>
          `;

          const popup = new maplibregl.Popup({ maxWidth: 'none', className: 'navik-tactical-popup' })
            .setLngLat(lngLat)
            .setDOMContent(popupDom)
            .addTo(map);
          popupRef.current = popup;

          getPointAnalytics(clickLat, clickLon)
            .then(res => {
              if (!popupRef.current || popupRef.current !== popup) return;
              const metrics = res?.metrics || {};
              const timestamp = res?.timestamp
                ? new Date(res.timestamp).toISOString().replace('T', ' ').slice(0, 19) + ' UTC'
                : new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
              const source = res?.source || res?.provenance?.source || 'INCOIS OPeNDAP & WaveWatch III';

              const getVal = (m, key1, key2) => {
                const v = m[key1] ?? m[key2];
                if (v && typeof v === 'object' && v.value != null) return Number(v.value);
                if (v != null && typeof v !== 'object') return Number(v);
                return null;
              };
              
              // Fisheries Phase F1 Payload adapter
              const prov = res?.provenance || {};
              // using existing source variable
              
              
              const safetyScore = res?.marine_severity_score;
              const fishingScore = res?.fishing_opportunity_score;
              const dataStatus = res?.data_status;
              
              // Only override HTML if we have real telemetry payload
              if (res && typeof res.marine_severity_score !== 'undefined') {
                  const safetyText = safetyScore !== null ? `<span class="text-[#FF5C5C] font-bold">Severity: ${safetyScore.toFixed(0)}/100</span>` : `<span class="text-[#8FA8B8]">BSI Data Unavailable</span>`;
                  const fishText = fishingScore !== null ? `<span class="text-[#18C7A0] font-bold">Opportunity: ${fishingScore.toFixed(0)}/100</span>` : `<span class="text-[#8FA8B8]">No PFZ Match</span>`;
                  
                  const sstVal = res.sst_c !== undefined && res.sst_c !== null ? `${res.sst_c.toFixed(1)}°C` : 'N/A';
                  const chlVal = res.chl_mg_m3 !== undefined && res.chl_mg_m3 !== null ? `${res.chl_mg_m3.toFixed(2)} mg/m³` : 'N/A';

                  popup.setHTML(`
                    <div class="bg-[#0D1B2A] border border-[#20384D] rounded-xl p-3 shadow-2xl min-w-[200px] text-left">
                      <div class="flex items-center space-x-2 mb-2 border-b border-[#20384D] pb-2">
                        <div class="h-2 w-2 rounded-full bg-[#00D4FF] shadow-[0_0_8px_#00D4FF]"></div>
                        <div class="text-[10px] text-[#00D4FF] font-bold uppercase tracking-wider">Ocean Analytics Point</div>
                      </div>
                      <div class="mb-3 text-[12px] space-y-1">
                        <div>Coordinates: <span class="text-[#EAF4F8] font-bold">${clickLat.toFixed(4)}°N, ${clickLon.toFixed(4)}°E</span></div>
                        <div class="text-[10px] text-[#8FA8B8] truncate">Source: ${source}</div>
                        <div class="text-[10px] text-[#8FA8B8] truncate">Status: ${dataStatus}</div>
                      </div>
                      <div class="flex justify-between items-center bg-[#13263A] rounded-lg p-2 mb-3">
                        <div class="flex flex-col text-[10px] space-y-1">
                           <div class="flex gap-4">
                             <span>SST: <span class="text-[#00D4FF] font-bold">${sstVal}</span></span>
                             <span>CHL: <span class="text-[#18C7A0] font-bold">${chlVal}</span></span>
                           </div>
                           <div class="border-t border-[#20384D] my-1 pt-1">
                             ${fishText}<br/>
                             ${safetyText}
                           </div>
                        </div>
                      </div>
                      <div class="flex space-x-2">
                        <button id="set-departure-${clickLat}-${clickLon}" class="flex-1 bg-[#20384D] hover:bg-[#18C7A0] hover:text-[#0D1B2A] text-[#EAF4F8] text-[10px] font-bold py-1.5 px-2 rounded-md transition-all duration-300 uppercase tracking-wider">
                          Dep
                        </button>
                        <button id="set-destination-${clickLat}-${clickLon}" class="flex-1 bg-[#00D4FF] hover:bg-[#EAF4F8] text-[#0D1B2A] text-[10px] font-bold py-1.5 px-2 rounded-md transition-all duration-300 shadow-[0_0_10px_rgba(0,212,255,0.3)] uppercase tracking-wider">
                          Dest
                        </button>
                      </div>
                    </div>
                  `);
                  
                  // Re-attach listeners
                  setTimeout(() => {
                    const depBtn = document.getElementById(`set-departure-${clickLat}-${clickLon}`);
                    const destBtn = document.getElementById(`set-destination-${clickLat}-${clickLon}`);
                    if (depBtn) depBtn.addEventListener('click', () => onLocationSelectRef.current({ lat: clickLat, lon: clickLon }));
                    if (destBtn) destBtn.addEventListener('click', () => onDestinationSelectRef.current({ lat: clickLat, lon: clickLon }));
                  }, 100);
                  
                  return;
              }
              const vSst = getVal(metrics, 'sst', 'sst_c');
              const vChl = getVal(metrics, 'chlorophyll', 'chl_mg_m3');
              const vWind = getVal(metrics, 'wind_speed', 'wind_speed_kmh');
              const vCurr = getVal(metrics, 'current_speed', 'current_speed_ms');
              const vWave = getVal(metrics, 'wave_height', 'wave_height_m');
              
              const sst = vSst != null ? `${vSst.toFixed(1)}°C` : 'N/A';
              const chl = vChl != null ? `${vChl.toFixed(2)} mg/m³` : 'N/A';
              const wind = vWind != null ? `${vWind.toFixed(1)} km/h` : 'N/A';
              const curr = vCurr != null ? `${vCurr.toFixed(2)} m/s` : 'N/A';
              const wave = vWave != null ? `${vWave.toFixed(2)} m` : 'N/A';

              popupDom.innerHTML = `
                <div class="bg-[#0D1B2A] text-[#EAF4F8] p-3.5 rounded-xl border border-[#20384D] font-sans shadow-2xl space-y-2.5" style="max-width: 300px;">
                  <div class="flex items-center justify-between border-b border-[#20384D] pb-1.5">
                    <span class="font-mono text-xs font-bold text-[#00D4FF]">Ocean Point Telemetry</span>
                    <span class="font-mono text-[9px] text-[#18C7A0] font-bold">INCOIS 0.1°</span>
                  </div>
                  
                  <div class="text-[10px] text-[#8FA8B8] space-y-1 font-medium">
                    <div class="flex justify-between font-mono">
                      <span>Coordinates:</span>
                      <span class="text-[#EAF4F8] font-bold">${clickLat.toFixed(4)}°N, ${clickLon.toFixed(4)}°E</span>
                    </div>
                    <div class="flex justify-between font-mono text-[9px]">
                      <span>Timestamp:</span>
                      <span class="text-[#8FA8B8]">${timestamp}</span>
                    </div>
                    <div class="flex justify-between font-mono text-[9px]">
                      <span>Source:</span>
                      <span class="text-[#18C7A0] truncate max-w-[170px]" title="${source}">${source}</span>
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-1.5 pt-1 text-[9px] font-mono bg-[#07111F] p-2 rounded-lg border border-[#20384D]/70">
                    <div class="flex items-center justify-between"><span class="text-[#8FA8B8]">Wind:</span> <span class="text-[#FFB547] font-bold">${wind}</span></div>
                    <div class="flex items-center justify-between"><span class="text-[#8FA8B8]">Current:</span> <span class="text-[#00D4FF] font-bold">${curr}</span></div>
                    <div class="flex items-center justify-between"><span class="text-[#8FA8B8]">SST:</span> <span class="text-[#FF5C5C] font-bold">${sst}</span></div>
                    <div class="flex items-center justify-between"><span class="text-[#8FA8B8]">CHL:</span> <span class="text-[#18C7A0] font-bold">${chl}</span></div>
                    <div class="col-span-2 flex items-center justify-between border-t border-[#20384D]/60 pt-1">
                      <span class="text-[#8FA8B8]">Wave Height (Hs):</span>
                      <span class="text-[#EAF4F8] font-bold">${wave}</span>
                    </div>
                  </div>

                  <div class="pt-1 flex gap-2">
                    <button
                      type="button"
                      id="btn-set-departure"
                      class="flex-1 py-1 px-2 rounded bg-[#18C7A0]/15 hover:bg-[#18C7A0]/25 border border-[#18C7A0]/40 text-[#18C7A0] font-mono text-[9px] font-bold transition cursor-pointer text-center"
                    >
                      Set Departure
                    </button>
                    <button
                      type="button"
                      id="btn-set-destination"
                      class="flex-1 py-1 px-2 rounded bg-[#00D4FF]/15 hover:bg-[#00D4FF]/25 border border-[#00D4FF]/40 text-[#00D4FF] font-mono text-[9px] font-bold transition cursor-pointer text-center"
                    >
                      Set Destination
                    </button>
                  </div>
                </div>
              `;

              const depBtn = popupDom.querySelector('#btn-set-departure');
              if (depBtn) {
                depBtn.addEventListener('click', () => {
                  if (onLocationSelectRef.current) {
                    onLocationSelectRef.current({ lat: clickLat, lon: clickLon });
                  }
                });
              }

              const destBtn = popupDom.querySelector('#btn-set-destination');
              if (destBtn) {
                destBtn.addEventListener('click', () => {
                  if (onDestinationSelectRef.current) {
                    onDestinationSelectRef.current({ lat: clickLat, lon: clickLon });
                  }
                });
              }
            })
            .catch(() => {
              if (!popupRef.current || popupRef.current !== popup) return;
              popupDom.innerHTML = `
                <div class="bg-[#0D1B2A] text-[#EAF4F8] p-3 rounded-lg border border-[#FF5C5C]/40 font-sans space-y-1.5" style="max-width: 240px;">
                  <span class="font-mono text-xs font-bold text-[#FF5C5C]">Telemetry Unavailable</span>
                  <p class="text-[10px] text-[#8FA8B8]">Data unavailable for coordinate ${clickLat.toFixed(4)}°N, ${clickLon.toFixed(4)}°E.</p>
                </div>
              `;
            });

          if (onLocationSelectRef.current && activeModeRef.current !== 'routing') {
            onLocationSelectRef.current({ lat: clickLat, lon: clickLon });
          }
        };

        // 1. BSI Grid Cell Click (triggers universal point telemetry)
        map.on('click', 'bsi-grid-fill', (e) => {
          handleOceanPointClick(e.lngLat);
        });

        map.on('mouseenter', 'bsi-grid-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'bsi-grid-fill', () => { map.getCanvas().style.cursor = ''; });

        // 2. Coastal District Advisory Click
        map.on('mouseenter', 'advisory-fill', () => { 
          map.getCanvas().style.cursor = 'pointer'; 
        });

        map.on('mousemove', 'advisory-fill', (e) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ['advisory-fill'] });
          if (!features.length) return;
          const props = features[0].properties || {};

          const district = props.DistrictNa || props.ENG || props.name || "Coastal Strip";
          const state = props.state || "";
          const suffix = getSuffix(beamWidthRef.current);
          const limitStr = suffix === '4' ? '4m' : suffix === '6' ? '6m' : '7m';

          let advisoryText = props[`ENG${suffix}`] || props[`HIN${suffix}`] || props.Advisory_E || "";
          advisoryText = advisoryText.trim();

          if (!advisoryText) {
            const warningColor = props[`Color${suffix}`];
            if (warningColor === 'Green' || warningColor === 'Safe' || !warningColor) {
              advisoryText = `${district} district, Boats less than ${limitStr} wide can safely sail.`;
            } else {
              advisoryText = "No advisory details available for this sector.";
            }
          }

          const cleanedAdvisory = advisoryText
            .replace(/<img[^>]*>/gi, '')
            .replace(/^(\s*<br\s*\/?>\s*)+/i, '')
            .replace(/font-size\s*:\s*[^;']*(px|rem|em)?/gi, 'font-size: 11px')
            .replace(/line-height\s*:\s*[^;']*(px|rem|em)?/gi, 'line-height: 1.3')
            .trim();

          if (popupRef.current) popupRef.current.remove();

          const popupContent = document.createElement('div');
          popupContent.className = 'bg-[#0D1B2A] text-[#EAF4F8] p-3.5 rounded-xl border border-[#20384D] font-sans shadow-2xl space-y-2';
          popupContent.style.maxWidth = '420px';
          popupContent.innerHTML = `
            <div class="flex items-center justify-between border-b border-[#20384D] pb-1.5">
              <span class="font-mono text-xs font-bold text-[#00D4FF]">${district} ${state ? `(${state})` : ''}</span>
              <span class="font-mono text-[9px] text-[#18C7A0] font-bold uppercase tracking-wider">INCOIS SVAS</span>
            </div>
            <div class="text-[11px] leading-relaxed text-[#8FA8B8] font-medium pt-1">
              ${cleanedAdvisory}
            </div>
          `;

          popupRef.current = new maplibregl.Popup({ maxWidth: 'none', closeButton: false, closeOnClick: false })
            .setLngLat(e.lngLat)
            .setDOMContent(popupContent)
            .addTo(map);
        });

        map.on('mouseleave', 'advisory-fill', () => { 
          map.getCanvas().style.cursor = ''; 
          if (popupRef.current) popupRef.current.remove();
        });

        map.on('click', 'advisory-fill', (e) => {
          if (onLocationSelectRef.current) {
            onLocationSelectRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng });
          }
        });

        // 3. Marine Protected Area (MPA) Click
        map.on('click', 'mpa-fill', (e) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ['mpa-fill'] });
          if (!features.length) return;
          const name = features[0].properties?.name || 'Marine Protected Sanctuary';

          if (popupRef.current) popupRef.current.remove();

          popupRef.current = new maplibregl.Popup({ maxWidth: 'none' })
            .setLngLat(e.lngLat)
            .setHTML(`
              <div class="bg-[#0D1B2A] text-[#EAF4F8] p-3 rounded-lg border border-[#a855f7]/40 font-sans space-y-1.5 shadow-2xl" style="max-width: 250px;">
                <h4 class="font-mono text-xs font-extrabold text-[#a855f7] border-b border-[#20384D] pb-1">Restricted Sanctuary (MPA)</h4>
                <p class="text-[10px] text-[#8FA8B8] leading-relaxed font-semibold">
                  ${name}<br>
                  <span class="text-[9px] text-[#FF5C5C] font-normal">Commercial fishing and non-authorized transit prohibited.</span>
                </p>
              </div>
            `)
            .addTo(map);

          if (onLocationSelectRef.current) {
            onLocationSelectRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng });
          }
        });

        map.on('mouseenter', 'mpa-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'mpa-fill', () => { map.getCanvas().style.cursor = ''; });

        // 4. PFZ Vector Line Click & Inspection
        map.on('click', 'pfz-lines-stroke', (e) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ['pfz-lines-stroke'] });
          if (!features.length) return;
          const feature = features[0];
          const props = feature.properties || {};
          const pfzId = feature.id || props.id || 'PFZ-Line';

          if (onPfzInspectRef.current) {
            onPfzInspectRef.current(feature);
          }

          if (popupRef.current) popupRef.current.remove();

          const vesselLat = selectedLocationRef.current?.lat ?? 18.96;
          const vesselLon = selectedLocationRef.current?.lon ?? 72.82;
          const clickLat = e.lngLat.lat;
          const clickLon = e.lngLat.lng;

          // Calculate approximate great-circle distance
          const dLat = (clickLat - vesselLat) * Math.PI / 180;
          const dLon = (clickLon - vesselLon) * Math.PI / 180;
          const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                    Math.cos(vesselLat * Math.PI / 180) * Math.cos(clickLat * Math.PI / 180) *
                    Math.sin(dLon / 2) * Math.sin(dLon / 2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
          const distanceKm = Math.round(6371 * c);

          const popupDom = document.createElement('div');
          popupDom.className = 'bg-[#0D1B2A] text-[#EAF4F8] p-3.5 rounded-xl border border-[#20384D] font-sans shadow-2xl space-y-2.5';
          popupDom.style.maxWidth = '280px';
          popupDom.innerHTML = `
            <div class="flex items-center justify-between border-b border-[#20384D] pb-1.5">
              <span class="font-mono text-xs font-bold text-[#FFB547]">PFZ High Catch Zone</span>
              <span class="font-mono text-[9px] text-[#8FA8B8]">INCOIS WFS</span>
            </div>
            <div class="text-[10px] text-[#8FA8B8] space-y-1 font-medium">
              <div class="flex justify-between"><span>Identifier:</span> <span class="font-mono text-[#EAF4F8] font-semibold">${pfzId}</span></div>
              <div class="flex justify-between"><span>Vessel Proximity:</span> <span class="font-mono text-[#00D4FF] font-bold">${distanceKm} km</span></div>
              <div class="flex justify-between"><span>SST Optimal Range:</span> <span class="font-mono text-[#18C7A0]">28°C — 30°C</span></div>
              <div class="flex justify-between"><span>Chlorophyll Front:</span> <span class="font-mono text-[#18C7A0]">High Gradient</span></div>
            </div>
            <div class="pt-1">
              <button 
                type="button"
                id="btn-navigate-pfz"
                class="w-full bg-[#00D4FF]/20 hover:bg-[#00D4FF]/30 border border-[#00D4FF]/50 text-[#00D4FF] text-[10px] font-mono font-bold py-1.5 rounded-lg transition-colors cursor-pointer text-center flex items-center justify-center gap-1.5"
              >
                Set as Route Target
              </button>
            </div>
          `;

          const navigateBtn = popupDom.querySelector('#btn-navigate-pfz');
          if (navigateBtn) {
            navigateBtn.addEventListener('click', () => {
              if (onDestinationSelectRef.current) {
                onDestinationSelectRef.current({ lat: clickLat, lon: clickLon });
              }
              if (popupRef.current) popupRef.current.remove();
            });
          }

          popupRef.current = new maplibregl.Popup({ maxWidth: 'none' })
            .setLngLat(e.lngLat)
            .setDOMContent(popupDom)
            .addTo(map);
        });

        map.on('mouseenter', 'pfz-lines-stroke', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'pfz-lines-stroke', () => { map.getCanvas().style.cursor = ''; });

        // 4.5. Route Node Interaction
        map.on('click', 'route-nodes-layer', (e) => {
          if (!e.features.length) return;
          const node = e.features[0];
          if (onNodeSelectRef.current) {
            onNodeSelectRef.current(node.id);
          }
        });
        map.on('mouseenter', 'route-nodes-layer', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'route-nodes-layer', () => { map.getCanvas().style.cursor = ''; });

        // 5. Universal Ocean Canvas Left-Click (Requirement R4)
        map.on('click', (e) => {
          // If clicked feature on interactive boundary/line layers, let feature-specific handlers handle it
          const features = map.queryRenderedFeatures(e.point, {
            layers: ['advisory-fill', 'mpa-fill', 'pfz-lines-stroke', 'route-nodes-layer'].filter(l => map.getLayer(l))
          });
          if (features.length > 0) return;

          handleOceanPointClick(e.lngLat);
        });

        setMapLoaded(true);
      } catch (err) {
        console.error('Error initializing map layers:', err);
      }
    });

    return () => {
      if (popupRef.current) {
        popupRef.current.remove();
        popupRef.current = null;
      }
      if (boatMarkerRef.current) {
        boatMarkerRef.current.remove();
        boatMarkerRef.current = null;
      }
      if (destMarkerRef.current) {
        destMarkerRef.current.remove();
        destMarkerRef.current = null;
      }
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  const onNodeSelectRef = useRef(onNodeSelect);
  useEffect(() => { onNodeSelectRef.current = onNodeSelect; }, [onNodeSelect]);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current || !routeData?.path) return;
    if (!mapRef.current.isStyleLoaded()) return;
    try {
      routeData.path.forEach(n => {
        mapRef.current.setFeatureState(
          { source: 'route-nodes', id: n.node_id },
          { selected: n.node_id === selectedNodeId }
        );
      });
    } catch (e) {
      console.warn('Map style not ready for setFeatureState', e);
    }
  }, [selectedNodeId, mapLoaded, routeData]);

  // 2. React to GeoJSON Prop Updates
  useEffect(() => {
    if (!mapLoaded) return;
    if (gridGeojson) {
      setSourceDataSafe('bsi-grid', gridGeojson);

      // The backend grid is now natively a dense 0.25 Point cloud, so we pipe it directly!
      // (This fixes the geometry.coordinates[0][0] crash since they are no longer polygons)
      setSourceDataSafe('bsi-points', gridGeojson);
    }
  }, [gridGeojson, mapLoaded, setSourceDataSafe]);

  useEffect(() => {
    if (!mapLoaded) return;
    if (advisoriesGeojson) setSourceDataSafe('coastal-advisories', advisoriesGeojson);
  }, [advisoriesGeojson, mapLoaded, setSourceDataSafe]);

  useEffect(() => {
    if (!mapLoaded) return;
    if (geofenceGeojson) setSourceDataSafe('geofencing-layers', geofenceGeojson);
  }, [geofenceGeojson, mapLoaded, setSourceDataSafe]);

  useEffect(() => {
    if (!mapLoaded) return;
    if (pfzGeojson) setSourceDataSafe('incois-pfz-lines', pfzGeojson);
  }, [pfzGeojson, mapLoaded, setSourceDataSafe]);

  useEffect(() => {
    if (!mapLoaded) return;
    if (vectorGrid?.windGeojson) {
      setSourceDataSafe('vector-wind', vectorGrid.windGeojson);
    }
    if (vectorGrid?.currentGeojson) {
      setSourceDataSafe('vector-current', vectorGrid.currentGeojson);
    }
  }, [vectorGrid, mapLoaded, setSourceDataSafe]);

  // 3. React to Route Data Prop Updates
  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;

    const routeCoords = routeData?.path?.map(n => [n.lon, n.lat]) || [];
    const straightCoords = routeCoords.length > 0 ? [routeCoords[0], routeCoords[routeCoords.length - 1]] : [];
    
    const routeGeo = routeCoords.length ? {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: routeCoords }
    } : EMPTY_FEATURE_COLLECTION;

    const straightGeo = straightCoords.length ? {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: straightCoords }
    } : EMPTY_FEATURE_COLLECTION;

    const nodesGeo = routeData?.path?.length ? {
      type: 'FeatureCollection',
      features: routeData.path.map(n => ({
        type: 'Feature',
        id: n.node_id,
        geometry: { type: 'Point', coordinates: [n.lon, n.lat] },
        properties: {
          node_id: n.node_id,
          eta: n.eta,
          severity_score: n.severity_score,
          color: n.severity_score >= 76 ? '#FF5C5C' : n.severity_score >= 51 ? '#FF5C5C' : n.severity_score >= 21 ? '#FFB547' : '#18C7A0'
        }
      }))
    } : EMPTY_FEATURE_COLLECTION;

    setSourceDataSafe('optimized-route', routeGeo);
    setSourceDataSafe('straight-route', straightGeo);
    setSourceDataSafe('route-nodes', nodesGeo);
  }, [routeData, mapLoaded, setSourceDataSafe]);

  // 4. Dynamic Mode-Based Layer Visibility Engine (via setLayoutProperty without canvas reload)
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;
    const hasRoute = Boolean(routeData?.path?.length);

    const modeVisibilityMap = {
      routing: {
        'route-line': hasRoute && layersOverride.route !== false ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route !== false ? 'visible' : 'none',
        'route-nodes-layer': hasRoute && layersOverride.route !== false ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none',
        'bsi-grid-fill': layersOverride.bsiRisk ? 'visible' : 'none',
        'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories ? 'visible' : 'none',
        'sst-raster': layersOverride.sst ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none',
        'wind-arrows': layersOverride.windVectors ? 'visible' : 'none',
        'current-arrows': layersOverride.currentVectors ? 'visible' : 'none'
      },
      fisheries: {
        'sst-raster': layersOverride.sst !== false ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll !== false ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory !== false ? 'visible' : 'none',
        'route-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none',
        'bsi-grid-fill': layersOverride.bsiRisk ? 'visible' : 'none',
        'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories ? 'visible' : 'none',
        'wind-arrows': layersOverride.windVectors ? 'visible' : 'none',
        'current-arrows': layersOverride.currentVectors ? 'visible' : 'none'
      },
      weather: {
        'bsi-grid-fill': layersOverride.bsiRisk !== false ? 'visible' : 'none',
        'bsi-heatmap': layersOverride.bsiRisk ? 'visible' : 'none',
        'advisory-fill': layersOverride.advisories !== false ? 'visible' : 'none',
        'advisory-stroke': layersOverride.advisories !== false ? 'visible' : 'none',
        'eez-stroke': layersOverride.eezBorder !== false ? 'visible' : 'none',
        'mpa-fill': layersOverride.restricted !== false ? 'visible' : 'none',
        'mpa-stroke': layersOverride.restricted !== false ? 'visible' : 'none',
        'sst-raster': layersOverride.sst ? 'visible' : 'none',
        'chl-raster': layersOverride.chlorophyll ? 'visible' : 'none',
        'pfz-lines-stroke': layersOverride.pfzAdvisory ? 'visible' : 'none',
        'wind-arrows': layersOverride.windVectors ? 'visible' : 'none',
        'current-arrows': layersOverride.currentVectors ? 'visible' : 'none',
        'route-line': hasRoute && layersOverride.route ? 'visible' : 'none',
        'straight-line': hasRoute && layersOverride.route ? 'visible' : 'none'
      }
    };

    const currentVisibility = modeVisibilityMap[activeMode] || modeVisibilityMap.routing;

    Object.entries(currentVisibility).forEach(([layerId, visibility]) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', visibility);
      }
    });
  }, [activeMode, layersOverride, mapLoaded, routeData]);

  // 5. Dynamic Raster Opacity (via setPaintProperty)
  useEffect(() => {
    if (mapRef.current && mapLoaded && mapRef.current.getLayer('sst-raster')) {
      mapRef.current.setPaintProperty('sst-raster', 'raster-opacity', sstOpacity);
    }
  }, [sstOpacity, mapLoaded]);

  useEffect(() => {
    if (mapRef.current && mapLoaded && mapRef.current.getLayer('chl-raster')) {
      mapRef.current.setPaintProperty('chl-raster', 'raster-opacity', chlOpacity);
    }
  }, [chlOpacity, mapLoaded]);

  // 6. Dynamic Coastal Advisory Paint Property per Beam Width
  useEffect(() => {
    if (mapRef.current && mapLoaded && mapRef.current.getLayer('advisory-fill')) {
      const suffix = getSuffix(beamWidth);
      mapRef.current.setPaintProperty('advisory-fill', 'fill-color', [
        'case',
        ['==', ['get', `Color${suffix}`], 'orange'], '#FFB547',
        ['==', ['get', `Color${suffix}`], 'red'], '#FF5C5C',
        '#18C7A0'
      ]);
      mapRef.current.setPaintProperty('advisory-stroke', 'line-color', [
        'case',
        ['==', ['get', `Color${suffix}`], 'orange'], '#FB923C',
        ['==', ['get', `Color${suffix}`], 'red'], '#F87171',
        '#4ADE80'
      ]);
    }
  }, [beamWidth, mapLoaded]);




  // 8. Vessel Marker Management (Draggable with dragend handler)
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    if (selectedLocation && selectedLocation.lat != null && selectedLocation.lon != null) {
      const coords = [selectedLocation.lon, selectedLocation.lat];

      if (boatMarkerRef.current) {
        boatMarkerRef.current.setLngLat(coords);
        // Smoothly fly to the new location if the user selects a distant port
        if (mapLoaded && mapRef.current) {
           mapRef.current.easeTo({ center: coords, speed: 0.8, curve: 1 });
        }
      } else {
        const el = document.createElement('div');
        el.className = 'custom-boat-marker group';
        el.style.width = '38px';
        el.style.height = '38px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.cursor = 'grab';
        el.style.filter = 'drop-shadow(0px 0px 8px rgba(0, 212, 255, 0.7))';
        el.innerHTML = `
          <img src="/boat_marker.svg" alt="Vessel Pointer" style="width: 100%; height: 100%; object-fit: contain; pointer-events: none;" />
        `;

        const marker = new maplibregl.Marker({ element: el, draggable: true })
          .setLngLat(coords)
          .addTo(mapRef.current);

        marker.on('dragend', () => {
          const lngLat = marker.getLngLat();
          if (onLocationSelectRef.current) {
            onLocationSelectRef.current({ lat: lngLat.lat, lon: lngLat.lng });
          }
        });

        boatMarkerRef.current = marker;
      }

      if (isInitialMountRef.current) {
        isInitialMountRef.current = false;
      }
    } else {
      if (boatMarkerRef.current) {
        boatMarkerRef.current.remove();
        boatMarkerRef.current = null;
      }
    }
  }, [selectedLocation, mapLoaded]);

  // 9. Destination Marker Management (Draggable with dragend handler)
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    const dest = destinationLocation || (
      routeData?.path?.length
        ? { lon: routeData.path[routeData.path.length - 1].lon, lat: routeData.path[routeData.path.length - 1].lat }
        : null
    );

    if (dest && dest.lat != null && dest.lon != null) {
      const coords = [dest.lon, dest.lat];

      if (destMarkerRef.current) {
        destMarkerRef.current.setLngLat(coords);
      } else {
        const el = document.createElement('div');
        el.className = 'custom-destination-marker';
        el.style.width = '38px';
        el.style.height = '38px';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.cursor = 'grab';
        el.style.filter = 'drop-shadow(0px 0px 8px rgba(255, 255, 255, 0.7))';
        el.innerHTML = `
          <img src="/destination.svg" alt="Destination Target" style="width: 100%; height: 100%; object-fit: contain; pointer-events: none;" />
        `;

        const marker = new maplibregl.Marker({ element: el, draggable: true })
          .setLngLat(coords)
          .addTo(mapRef.current);

        marker.on('dragend', () => {
          const lngLat = marker.getLngLat();
          if (onDestinationSelectRef.current) {
            onDestinationSelectRef.current({ lat: lngLat.lat, lon: lngLat.lng });
          }
        });

        destMarkerRef.current = marker;
      }
    } else {
      if (destMarkerRef.current) {
        destMarkerRef.current.remove();
        destMarkerRef.current = null;
      }
    }
  }, [destinationLocation, routeData, mapLoaded]);

  return (
    <div className={`w-full h-full relative bg-[#07111F] overflow-hidden ${className}`}>
      {/* MapLibre WebGL Canvas Container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Floating Tactical Legend Overlay */}
      <MapLegend activeMode={activeMode} />
    </div>
  );
}

export default MapConsole;
