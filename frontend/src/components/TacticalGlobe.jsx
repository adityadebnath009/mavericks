import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Compass, Eye, RotateCw, Pause, Play, ShieldAlert, Navigation, Activity } from 'lucide-react';

// World and regional landmass polygon approximation coordinates (lon, lat in degrees)
// Designed specifically for high-contrast tactical naval projection centered on Indian Ocean & global seas
const LANDMASS_POLYGONS = [
  // Indian Subcontinent (detailed tactical contour)
  [
    [68.1, 23.7], [70.5, 21.0], [72.8, 19.0], [73.8, 15.5], [75.0, 13.0], 
    [76.5, 10.0], [77.5, 8.1], [78.2, 9.2], [79.8, 10.8], [80.3, 13.1], 
    [82.0, 16.0], [83.3, 17.7], [85.0, 19.5], [86.9, 20.8], [89.0, 21.8], 
    [90.5, 23.0], [88.5, 26.0], [84.0, 27.5], [80.5, 29.0], [77.0, 31.0], 
    [74.0, 34.0], [72.0, 30.0], [70.0, 27.0], [68.1, 23.7]
  ],
  // Sri Lanka
  [
    [79.8, 9.8], [81.8, 8.6], [81.7, 6.9], [80.5, 5.9], [79.7, 6.9], [79.8, 9.8]
  ],
  // Andaman & Nicobar Ridge
  [
    [92.7, 13.5], [93.0, 11.5], [93.8, 7.0], [93.5, 6.8], [92.6, 11.5], [92.7, 13.5]
  ],
  // Arabian Peninsula & Persian Gulf
  [
    [36.0, 28.0], [40.0, 22.0], [43.0, 13.5], [50.0, 14.0], [54.0, 17.0], 
    [59.5, 22.5], [56.5, 26.0], [50.0, 28.0], [48.0, 30.0], [40.0, 31.0], [36.0, 28.0]
  ],
  // Africa East Coast & Horn of Africa
  [
    [32.0, 31.0], [35.0, 25.0], [39.0, 16.0], [43.5, 12.0], [51.2, 10.5], 
    [48.0, 3.0], [41.0, -4.0], [39.0, -10.0], [35.0, -20.0], [32.5, -28.0], 
    [28.0, -33.0], [20.0, -34.5], [18.0, -34.0], [18.0, -20.0], [12.0, -10.0], 
    [9.0, 4.0], [0.0, 6.0], [-15.0, 12.0], [-17.0, 15.0], [-15.0, 24.0], 
    [-5.0, 35.0], [10.0, 37.0], [25.0, 32.0], [32.0, 31.0]
  ],
  // Madagascar
  [
    [49.5, -12.5], [50.5, -16.0], [47.5, -25.0], [44.0, -25.2], [44.0, -16.0], [49.5, -12.5]
  ],
  // Southeast Asia & Indochina
  [
    [92.0, 21.0], [98.0, 16.0], [100.0, 8.0], [103.0, 1.3], [104.0, 10.0], 
    [109.0, 12.0], [108.0, 20.0], [105.0, 22.0], [95.0, 24.0], [92.0, 21.0]
  ],
  // Indonesia / Sumatra / Java
  [
    [95.5, 5.5], [98.5, 3.0], [104.5, -5.0], [106.0, -6.0], [114.0, -8.0], 
    [115.0, -8.5], [108.0, -7.0], [100.0, -1.0], [95.5, 5.5]
  ],
  // Australia
  [
    [114.0, -22.0], [113.0, -26.0], [115.0, -34.0], [122.0, -34.0], [138.0, -35.0], 
    [148.0, -38.0], [153.0, -28.0], [145.0, -15.0], [136.0, -12.0], [130.0, -13.0], 
    [122.0, -17.0], [114.0, -22.0]
  ],
  // Europe & Mediterranean Basin
  [
    [-9.0, 37.0], [-9.0, 43.0], [0.0, 48.0], [5.0, 53.0], [10.0, 54.0], 
    [20.0, 55.0], [28.0, 41.0], [22.0, 38.0], [14.0, 37.0], [5.0, 43.0], 
    [-3.0, 36.0], [-9.0, 37.0]
  ],
  // East Asia & Japan
  [
    [120.0, 40.0], [129.0, 35.0], [135.0, 35.0], [141.0, 43.0], [140.0, 36.0], 
    [130.0, 31.0], [121.0, 31.0], [118.0, 24.0], [120.0, 40.0]
  ]
];

// Tactical Maritime Routes (Indian Ocean Operations)
const TACTICAL_ROUTES = [
  {
    id: 'route-kochi-lakshadweep',
    name: 'Kochi ➔ Lakshadweep (Kavaratti)',
    from: { name: 'Kochi Port', lon: 76.26, lat: 9.93 },
    to: { name: 'Kavaratti', lon: 72.64, lat: 10.56 },
    color: '#00D4FF', // Cyan optimal vector
    status: 'OPTIMAL // CURRENT-ASSISTED',
    dist: '215 NM',
    saving: '+18% Fuel Eff.',
    waypoints: [
      { lon: 76.26, lat: 9.93 },
      { lon: 75.30, lat: 10.15 },
      { lon: 74.10, lat: 10.35 },
      { lon: 72.64, lat: 10.56 }
    ]
  },
  {
    id: 'route-mumbai-porbandar',
    name: 'Mumbai ➔ Porbandar Coastal',
    from: { name: 'Mumbai Harbor', lon: 72.83, lat: 18.94 },
    to: { name: 'Porbandar', lon: 69.60, lat: 21.64 },
    color: '#18C7A0', // Sea Green safe vector
    status: 'SAFE ROUTE // COASTAL GEOFENCE CLEAR',
    dist: '290 NM',
    saving: 'Clear of Swell Hazard',
    waypoints: [
      { lon: 72.83, lat: 18.94 },
      { lon: 72.20, lat: 19.80 },
      { lon: 71.10, lat: 20.60 },
      { lon: 69.60, lat: 21.64 }
    ]
  },
  {
    id: 'route-chennai-portblair',
    name: 'Chennai ➔ Port Blair (Andamans)',
    from: { name: 'Chennai Port', lon: 80.27, lat: 13.08 },
    to: { name: 'Port Blair', lon: 92.74, lat: 11.66 },
    color: '#00D4FF',
    status: 'DIURNAL DEPARTURE WINDOW: +2H',
    dist: '740 NM',
    saving: 'Wave Steepness 0.012 (Optimal)',
    waypoints: [
      { lon: 80.27, lat: 13.08 },
      { lon: 83.50, lat: 12.80 },
      { lon: 87.00, lat: 12.30 },
      { lon: 90.50, lat: 11.90 },
      { lon: 92.74, lat: 11.66 }
    ]
  },
  {
    id: 'route-vizag-paradip',
    name: 'Visakhapatnam ➔ Paradip',
    from: { name: 'Vizag Outer', lon: 83.21, lat: 17.68 },
    to: { name: 'Paradip Port', lon: 86.67, lat: 20.26 },
    color: '#18C7A0',
    status: 'LOW RISK // BSI 1/7',
    dist: '240 NM',
    saving: 'EEZ Border Buffer: 116.9 km',
    waypoints: [
      { lon: 83.21, lat: 17.68 },
      { lon: 84.40, lat: 18.50 },
      { lon: 85.60, lat: 19.40 },
      { lon: 86.67, lat: 20.26 }
    ]
  }
];

// Simulated Live Tactical Fleet
const SIMULATED_VESSELS = [
  {
    id: 'SK-104',
    name: 'Sagar Kanya (Research Vessel)',
    lon: 74.5,
    lat: 14.8,
    speed: '12.4 kn',
    heading: '284°',
    status: 'ONLINE',
    color: '#00D4FF'
  },
  {
    id: 'MV-082',
    name: 'Matsya Vigyan (Fisheries)',
    lon: 82.8,
    lat: 12.2,
    speed: '10.8 kn',
    heading: '045°',
    status: 'SURVEY',
    color: '#18C7A0'
  },
  {
    id: 'ICG-204',
    name: 'ICG Varad (Patrol)',
    lon: 69.1,
    lat: 21.1,
    speed: '18.2 kn',
    heading: '160°',
    status: 'ENFORCING',
    color: '#00D4FF'
  },
  {
    id: 'SR-019',
    name: 'Samudra Ratnakar',
    lon: 87.2,
    lat: 19.8,
    speed: '11.5 kn',
    heading: '210°',
    status: 'TRANSIT',
    color: '#18C7A0'
  }
];

// Hazard & Restricted Zones
const TACTICAL_ZONES = [
  {
    id: 'mpa-gulf-mannar',
    name: 'Gulf of Mannar Biosphere',
    type: 'RESTRICTED MPA GEOFENCE',
    lon: 79.1,
    lat: 9.1,
    radiusDeg: 1.2,
    color: '#FF5C5C', // Coral Red restricted boundary
    label: 'RESTRICTED MPA'
  },
  {
    id: 'mpa-sundarbans',
    name: 'Sundarbans Marine Eco-Zone',
    type: 'RESTRICTED SANCTUARY',
    lon: 88.8,
    lat: 21.6,
    radiusDeg: 1.2,
    color: '#FF5C5C', // Coral Red restricted boundary
    label: 'RESTRICTED ZONE'
  },
  {
    id: 'hazard-gujarat-swell',
    name: 'Gujarat Coast Wave Hazard',
    type: 'HIGH WAVE WARNING (Hs >= 3.5m)',
    lon: 68.5,
    lat: 20.8,
    radiusDeg: 1.4,
    color: '#FF5C5C', // Coral Red
    label: 'RESTRICTED SWELL ZONE'
  }
];

export default function TacticalGlobe({ onSelectRoute, onLaunchConsole }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Rotation angles in radians stored in refs to avoid 60Hz React component re-renders
  // Default centered on Indian Ocean (Lon ~77°E, Lat ~16°N)
  const rotYRef = useRef(-1.35); // Yaw (~77° East)
  const rotXRef = useRef(0.28);  // Pitch (~16° North tilt)
  const isRotatingRef = useRef(true);
  const isDraggingRef = useRef(false);
  const activeRouteIndexRef = useRef(0);
  const [isRotating, setIsRotating] = useState(true);
  const [activeRouteIndex, setActiveRouteIndex] = useState(0);
  const [canvasAvailable, setCanvasAvailable] = useState(true);

  const dragStartRef = useRef({ x: 0, y: 0, rotY: -1.35, rotX: 0.28 });
  const animFrameRef = useRef(null);
  const pulsePhaseRef = useRef(0);

  // Keep refs synchronized with UI state
  useEffect(() => {
    isRotatingRef.current = isRotating;
  }, [isRotating]);

  useEffect(() => {
    activeRouteIndexRef.current = activeRouteIndex;
  }, [activeRouteIndex]);

  // Helper 3D Projection Math
  // lon/lat in degrees -> 3D sphere coordinate -> rotated -> 2D screen coordinate
  const project3D = useCallback((lon, lat, radius, cx, cy, yaw, pitch) => {
    const lambda = (lat * Math.PI) / 180;
    const mu = (lon * Math.PI) / 180;

    // 1. Base Cartesian (Y is up, Z is towards viewer)
    const x0 = radius * Math.cos(lambda) * Math.sin(mu);
    const y0 = -radius * Math.sin(lambda);
    const z0 = radius * Math.cos(lambda) * Math.cos(mu);

    // 2. Rotate around Y (Yaw)
    const x1 = x0 * Math.cos(yaw) + z0 * Math.sin(yaw);
    const z1 = -x0 * Math.sin(yaw) + z0 * Math.cos(yaw);

    // 3. Rotate around X (Pitch)
    const y2 = y0 * Math.cos(pitch) - z1 * Math.sin(pitch);
    const z2 = y0 * Math.sin(pitch) + z1 * Math.cos(pitch);

    // Visible if z2 > 0 (front hemisphere)
    return {
      x: cx + x1,
      y: cy + y2,
      z: z2,
      visible: z2 > 0,
      depthRatio: (z2 + radius) / (2 * radius) // 0 to 1
    };
  }, []);

  // Main Canvas Render Loop
  useEffect(() => {
    let lastTime = performance.now();

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) {
        animFrameRef.current = requestAnimationFrame(render);
        return;
      }
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        animFrameRef.current = requestAnimationFrame(render);
        return;
      }

      const currentTime = performance.now();
      const dt = Math.min((currentTime - lastTime) / 1000, 0.1);
      lastTime = currentTime;

      // Update pulse phase
      pulsePhaseRef.current = (pulsePhaseRef.current + dt * 0.8) % 1;

      // Auto-rotation (tactical, gentle ~0.045 rad/s)
      if (isRotatingRef.current && !isDraggingRef.current) {
        rotYRef.current -= dt * 0.045;
      }

      const curRotY = rotYRef.current;
      const curRotX = rotXRef.current;
      const curActiveIdx = activeRouteIndexRef.current;

      // Handle Canvas DPI and resize safely
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      // Debug telemetry (approx. once every 100 frames)
      if (Math.random() < 0.01) {
        console.log("[TacticalGlobe HUD] Loop active:", {
          dimensions: `${width}x${height}`,
          yaw: curRotY.toFixed(3),
          dt: dt.toFixed(4),
          isRotating: isRotatingRef.current,
          isDragging: isDraggingRef.current
        });
      }

      // Guard against zero dimensions during initial mount/unmount
      if (width <= 10 || height <= 10) {
        animFrameRef.current = requestAnimationFrame(render);
        return;
      }

      const dpr = window.devicePixelRatio || 1;

      if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;
      const radius = Math.min(width, height) * 0.40;

      // 1. Atmosphere Halo (Cyan Neon Glow)
      const glowGrad = ctx.createRadialGradient(cx, cy, radius * 0.95, cx, cy, radius * 1.25);
      glowGrad.addColorStop(0, 'rgba(0, 212, 255, 0.22)');
      glowGrad.addColorStop(0.4, 'rgba(0, 212, 255, 0.08)');
      glowGrad.addColorStop(1, 'rgba(7, 17, 31, 0)');
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.25, 0, Math.PI * 2);
      ctx.fill();

      // 2. Base Sphere Ocean Fill (Desaturated Dark Navy Shading)
      const sphereGrad = ctx.createRadialGradient(
        cx - radius * 0.35, 
        cy - radius * 0.35, 
        radius * 0.1, 
        cx, 
        cy, 
        radius
      );
      sphereGrad.addColorStop(0, '#0D2638'); // Ocean highlight
      sphereGrad.addColorStop(0.65, '#07111F'); // Deep Navy body
      sphereGrad.addColorStop(1, '#040910'); // Outer rim shadow

      ctx.fillStyle = sphereGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();

      // Sphere Outer Boundary Stroke
      ctx.strokeStyle = '#20384D';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.stroke();

      // Clip all internal rendering to the sphere disk for zero rim bleeding
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.clip();

      // 3. Coordinate Grid (Parallels & Meridians)
      ctx.strokeStyle = '#20384D';
      ctx.lineWidth = 0.8;

      // Latitudes (-60, -30, 0, 30, 60)
      const latSteps = [-60, -30, 0, 30, 60];
      latSteps.forEach(lat => {
        ctx.beginPath();
        let started = false;
        for (let lon = -180; lon <= 180; lon += 5) {
          const pt = project3D(lon, lat, radius, cx, cy, curRotY, curRotX);
          if (pt.visible) {
            if (!started) {
              ctx.moveTo(pt.x, pt.y);
              started = true;
            } else {
              ctx.lineTo(pt.x, pt.y);
            }
          } else {
            started = false;
          }
        }
        ctx.stroke();
      });

      // Longitudes (every 30 deg)
      for (let lon = -180; lon < 180; lon += 30) {
        ctx.beginPath();
        let started = false;
        for (let lat = -80; lat <= 80; lat += 4) {
          const pt = project3D(lon, lat, radius, cx, cy, curRotY, curRotX);
          if (pt.visible) {
            if (!started) {
              ctx.moveTo(pt.x, pt.y);
              started = true;
            } else {
              ctx.lineTo(pt.x, pt.y);
            }
          } else {
            started = false;
          }
        }
        ctx.stroke();
      }

      // 4. Landmass Polygons (Subdued Ocean Slate #13263A)
      LANDMASS_POLYGONS.forEach(polygon => {
        // Collect visible projected points
        const points = polygon.map(([lon, lat]) => project3D(lon, lat, radius, cx, cy, curRotY, curRotX));
        
        // Count how many are visible
        const visibleCount = points.filter(p => p.visible).length;
        if (visibleCount > 2) {
          ctx.beginPath();
          let first = true;
          points.forEach(p => {
            if (p.visible) {
              if (first) {
                ctx.moveTo(p.x, p.y);
                first = false;
              } else {
                ctx.lineTo(p.x, p.y);
              }
            }
          });
          ctx.closePath();
          ctx.fillStyle = '#13263A';
          ctx.fill();
          ctx.strokeStyle = '#20384D';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      });

      // 5. Tactical Zones & Geofences (MPAs & Hazard Rings)
      TACTICAL_ZONES.forEach(zone => {
        const center = project3D(zone.lon, zone.lat, radius, cx, cy, curRotY, curRotX);
        if (center.visible) {
          const ringRad = zone.radiusDeg * (radius / 90);
          
          ctx.save();
          ctx.strokeStyle = zone.color;
          ctx.setLineDash([4, 3]);
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(center.x, center.y, ringRad, 0, Math.PI * 2);
          ctx.stroke();

          // Fill tint
          ctx.fillStyle = zone.color === '#FF5C5C' ? 'rgba(255, 92, 92, 0.12)' : 'rgba(255, 181, 71, 0.12)';
          ctx.fill();

          // Zone Tag Label
          ctx.font = '9px "JetBrains Mono", monospace';
          ctx.fillStyle = zone.color;
          ctx.fillText(zone.label, center.x + ringRad + 4, center.y + 3);
          ctx.restore();
        }
      });

      // 6. Tactical Maritime Routes (3D Vector Arcs)
      TACTICAL_ROUTES.forEach((route, idx) => {
        const isCurrentActive = idx === curActiveIdx;
        const color = route.color;

        // Interpolate smooth curve points
        const curvePoints = [];
        const steps = 30;
        for (let i = 0; i <= steps; i++) {
          const t = i / steps;
          // Interpolate across waypoints
          const wpIdx = Math.min(
            Math.floor(t * (route.waypoints.length - 1)), 
            route.waypoints.length - 2
          );
          const localT = (t * (route.waypoints.length - 1)) - wpIdx;
          
          const pA = route.waypoints[wpIdx];
          const pB = route.waypoints[wpIdx + 1];
          
          const curLon = pA.lon + (pB.lon - pA.lon) * localT;
          const curLat = pA.lat + (pB.lat - pA.lat) * localT;
          
          // Slight altitude elevation for tactical arc
          const elevRadius = radius * (1 + 0.018 * Math.sin(t * Math.PI));
          const pt = project3D(curLon, curLat, elevRadius, cx, cy, curRotY, curRotX);
          curvePoints.push({ ...pt, t });
        }

        // Draw Base Route Arc
        ctx.beginPath();
        let pathStarted = false;
        curvePoints.forEach(pt => {
          if (pt.visible) {
            if (!pathStarted) {
              ctx.moveTo(pt.x, pt.y);
              pathStarted = true;
            } else {
              ctx.lineTo(pt.x, pt.y);
            }
          } else {
            pathStarted = false;
          }
        });

        ctx.strokeStyle = color;
        ctx.lineWidth = isCurrentActive ? 2.5 : 1.2;
        ctx.globalAlpha = isCurrentActive ? 0.95 : 0.6;
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        // Animated Energy Pulse along the active route
        if (isCurrentActive) {
          const pulseT = pulsePhaseRef.current;
          const pulseIdx = Math.floor(pulseT * (curvePoints.length - 1));
          const pulsePt = curvePoints[pulseIdx];

          if (pulsePt && pulsePt.visible) {
            // Glowing pulse head
            const pGrad = ctx.createRadialGradient(pulsePt.x, pulsePt.y, 1, pulsePt.x, pulsePt.y, 8);
            pGrad.addColorStop(0, '#FFFFFF');
            pGrad.addColorStop(0.4, '#00D4FF');
            pGrad.addColorStop(1, 'rgba(0, 212, 255, 0)');
            
            ctx.fillStyle = pGrad;
            ctx.beginPath();
            ctx.arc(pulsePt.x, pulsePt.y, 8, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = '#FFFFFF';
            ctx.beginPath();
            ctx.arc(pulsePt.x, pulsePt.y, 2.5, 0, Math.PI * 2);
            ctx.fill();
          }
        }

        // Waypoint markers (Start / End)
        const startPt = project3D(route.from.lon, route.from.lat, radius, cx, cy, curRotY, curRotX);
        const endPt = project3D(route.to.lon, route.to.lat, radius, cx, cy, curRotY, curRotX);

        if (startPt.visible) {
          ctx.fillStyle = '#18C7A0'; // Start Sea Green
          ctx.beginPath();
          ctx.arc(startPt.x, startPt.y, 3, 0, Math.PI * 2);
          ctx.fill();
        }

        if (endPt.visible) {
          ctx.fillStyle = '#FFFFFF'; // Destination White
          ctx.beginPath();
          ctx.arc(endPt.x, endPt.y, 3.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#00D4FF';
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }
      });

      // 7. Simulated Live Fleet Markers
      SIMULATED_VESSELS.forEach(vessel => {
        const pos = project3D(vessel.lon, vessel.lat, radius * 1.01, cx, cy, curRotY, curRotX);
        if (pos.visible) {
          // Pulsing Beacon Ring in Neon Cyan (#00D4FF) - Linear radar wave (always positive to prevent IndexSizeError)
          const pulseRadius = 3 + 7 * pulsePhaseRef.current;
          ctx.strokeStyle = '#00D4FF';
          ctx.lineWidth = 1.2;
          ctx.globalAlpha = Math.max(0.1, 0.9 * (1 - pulsePhaseRef.current));
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, pulseRadius, 0, Math.PI * 2);
          ctx.stroke();
          ctx.globalAlpha = 1.0;

          // Vessel Marker: Off White (#EAF4F8) center dot with sharp Cyan outline
          ctx.fillStyle = '#EAF4F8';
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, 3, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = '#00D4FF';
          ctx.lineWidth = 1;
          ctx.stroke();

          // Vessel Tactical Tag
          ctx.font = '8px "JetBrains Mono", monospace';
          ctx.fillStyle = '#EAF4F8';
          ctx.fillText(`[${vessel.id}]`, pos.x + 7, pos.y - 4);
          ctx.fillStyle = '#8FA8B8';
          ctx.fillText(`${vessel.speed}`, pos.x + 7, pos.y + 6);
        }
      });

      ctx.restore(); // Restore from clipping mask

      // 8. Atmospheric Glow Rim Arc (Sharp Neon Edge)
      ctx.strokeStyle = 'rgba(0, 212, 255, 0.45)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, radius + 1, -Math.PI * 0.75, Math.PI * 0.25);
      ctx.stroke();

      ctx.restore();

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, []);

  // Unified Pointer Drag Handlers (Mouse, Touch, Stylus with Pointer Capture)
  const handlePointerDown = (e) => {
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch (_) {}
    isDraggingRef.current = true;
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      rotY: rotYRef.current,
      rotX: rotXRef.current
    };
  };

  const handlePointerMove = (e) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    
    // Convert screen drag delta to rotation
    rotYRef.current = dragStartRef.current.rotY + dx * 0.006;
    // Limit pitch to prevent flipping
    const newPitch = Math.max(-0.8, Math.min(0.8, dragStartRef.current.rotX + dy * 0.006));
    rotXRef.current = newPitch;
  };

  const handlePointerUp = (e) => {
    try {
      if (e.currentTarget.hasPointerCapture(e.pointerId)) {
        e.currentTarget.releasePointerCapture(e.pointerId);
      }
    } catch (_) {}
    isDraggingRef.current = false;
  };

  const resetOrientation = () => {
    rotYRef.current = -1.35;
    rotXRef.current = 0.28;
  };

  const activeRoute = TACTICAL_ROUTES[activeRouteIndex];

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-[460px] lg:h-[540px] bg-[#07111F] rounded-2xl border border-[#20384D] overflow-hidden flex flex-col justify-between select-none shadow-2xl touch-none"
    >
      {/* Tactical Top Bar Overlay */}
      <div className="absolute top-0 left-0 right-0 z-10 px-4 py-3 bg-gradient-to-b from-[#0D1B2A]/90 to-transparent flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#00D4FF] animate-pulse" />
          <span className="text-[11px] font-mono font-bold tracking-widest text-[#EAF4F8] uppercase">
            3D TACTICAL SPATIAL ENGINE
          </span>
          <span className="hidden sm:inline-block text-[9px] font-mono px-2 py-0.5 rounded bg-[#13263A] text-[#8FA8B8] border border-[#20384D]">
            ORTHOGRAPHIC PROJECTION // 0.4° GRID
          </span>
        </div>

        <div className="pointer-events-auto flex items-center gap-1.5 bg-[#0D1B2A]/80 backdrop-blur-sm border border-[#20384D] rounded-lg p-1">
          <button
            onClick={() => setIsRotating(prev => !prev)}
            className="p-1 text-[#8FA8B8] hover:text-[#00D4FF] transition-colors rounded hover:bg-[#13263A] cursor-pointer"
            title={isRotating ? "Pause Auto-Rotation" : "Resume Auto-Rotation"}
          >
            {isRotating ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={resetOrientation}
            className="p-1 text-[#8FA8B8] hover:text-[#00D4FF] transition-colors rounded hover:bg-[#13263A] cursor-pointer"
            title="Reset Indian Ocean Center"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main HTML5 Canvas / Graceful Fallback */}
      {canvasAvailable ? (
        <canvas
          ref={canvasRef}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="w-full h-full cursor-grab active:cursor-grabbing touch-none"
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center space-y-3 font-mono">
          <Activity className="w-12 h-12 text-[#00D4FF] animate-pulse" />
          <div className="text-sm font-bold text-[#EAF4F8]">TACTICAL RADAR BACKUP ACTIVE</div>
          <p className="text-xs text-[#8FA8B8] max-w-xs">
            Simulation mesh running in high-contrast fallback mode. Active Indian Ocean fleet: 104 vessels.
          </p>
        </div>
      )}

      {/* Corner Tactical Reticles */}
      <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-[#00D4FF]/40 pointer-events-none" />
      <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-[#00D4FF]/40 pointer-events-none" />
      <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-[#00D4FF]/40 pointer-events-none" />
      <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-[#00D4FF]/40 pointer-events-none" />

      {/* Active Route Tactical Telemetry Card (Floating Bottom Overlay) */}
      <div className="absolute bottom-3 left-3 right-3 z-10 bg-[#0D1B2A]/90 backdrop-blur-md border border-[#20384D] rounded-xl p-3 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2 border-b border-[#20384D]">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase text-[#8FA8B8]">Active Route Vector:</span>
            <span className="text-xs font-bold text-[#EAF4F8]">{activeRoute.name}</span>
          </div>

          <div className="flex items-center gap-1">
            {TACTICAL_ROUTES.map((route, i) => (
              <button
                key={route.id}
                onClick={() => {
                  setActiveRouteIndex(i);
                  if (onSelectRoute) onSelectRoute(route);
                }}
                className={`px-2 py-0.5 text-[10px] font-mono rounded transition-all cursor-pointer ${
                  activeRouteIndex === i
                    ? 'bg-[#00D4FF] text-[#07111F] font-bold shadow-sm'
                    : 'bg-[#13263A] text-[#8FA8B8] hover:text-[#EAF4F8] border border-[#20384D]'
                }`}
              >
                V-0{i + 1}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
          <div className="bg-[#13263A]/80 p-1.5 rounded border border-[#20384D]">
            <span className="text-[9px] text-[#8FA8B8] block uppercase">Route Status</span>
            <span className="text-[#00D4FF] font-semibold truncate block">{activeRoute.status}</span>
          </div>
          <div className="bg-[#13263A]/80 p-1.5 rounded border border-[#20384D]">
            <span className="text-[9px] text-[#8FA8B8] block uppercase">Distance</span>
            <span className="text-[#EAF4F8] font-bold block">{activeRoute.dist}</span>
          </div>
          <div className="bg-[#13263A]/80 p-1.5 rounded border border-[#20384D]">
            <span className="text-[9px] text-[#8FA8B8] block uppercase">Optimization</span>
            <span className="text-[#18C7A0] font-semibold truncate block">{activeRoute.saving}</span>
          </div>
          <div className="bg-[#13263A]/80 p-1.5 rounded border border-[#20384D] flex items-center justify-between">
            <div>
              <span className="text-[9px] text-[#8FA8B8] block uppercase">Sim Fleet</span>
              <span className="text-[#EAF4F8] font-semibold">104 Vessels</span>
            </div>
            <button
              onClick={onLaunchConsole}
              className="text-[9px] bg-[#00D4FF]/10 text-[#00D4FF] hover:bg-[#00D4FF]/20 border border-[#00D4FF]/30 px-2 py-1 rounded transition-colors font-bold cursor-pointer"
            >
              TRACK ➔
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
