import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Polygon, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

/**
 * Frozen Navik Design System Map Palette Constants (GEMINI.md §4)
 */
export const NAVIK_MAP_STYLES = {
  containerBackground: '#07111F', // Deep Navy base surface
  tileLayer: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19,
  },
  routes: {
    active: {
      color: '#00D4FF', // Frozen Navik Cyan primary accent
      weight: 4,
      opacity: 0.95,
      lineCap: 'round',
      lineJoin: 'round',
    },
    alternate: {
      color: '#64748b', // Secondary Slate
      weight: 2,
      opacity: 0.8,
      dashArray: '5, 5',
    },
  },
  geofences: {
    restricted: {
      color: '#FF5C5C', // Frozen Navik Coral Red
      fillColor: '#FF5C5C',
      fillOpacity: 0.25,
      weight: 2,
      dashArray: '4, 4',
    },
    eez: {
      color: '#FF5C5C',
      weight: 2,
      dashArray: '6, 4',
      opacity: 0.85,
    },
  },
  markers: {
    vessel: {
      color: '#00D4FF', // Cyan accent
      size: 24,
    },
    start: {
      color: '#18C7A0', // Sea Green
      size: 16,
    },
    destination: {
      color: '#FFFFFF', // Pure White
      borderColor: '#00D4FF',
      size: 18,
    },
    pfz: {
      color: '#FFB547', // Amber warning/advisory
      fillColor: '#FFB547',
      radius: 6,
    },
  },
};

const DEFAULT_CENTER = [15.0, 75.0];
const DEFAULT_ZOOM = 6;

/**
 * Safely parse coordinate input into a [lat, lon] tuple of finite numbers.
 * Supports:
 * - [lat, lon] numeric arrays
 * - ["15.0", "75.0"] string arrays
 * - { lat, lon } or { lat, lng } or { latitude, longitude } objects
 * Returns null if input is incomplete, malformed, empty, or non-numeric.
 * ZERO spherical math or trigonometric calculations performed.
 */
export const parseLatLng = (pt) => {
  if (!pt) return null;

  let rawLat;
  let rawLon;

  if (Array.isArray(pt)) {
    if (pt.length < 2) return null;
    rawLat = pt[0];
    rawLon = pt[1];
  } else if (typeof pt === 'object') {
    rawLat = pt.lat !== undefined ? pt.lat : pt.latitude;
    rawLon = pt.lon !== undefined ? pt.lon : (pt.lng !== undefined ? pt.lng : pt.longitude);
  } else {
    return null;
  }

  if (rawLat == null || rawLon == null) return null;
  if (typeof rawLat === 'string' && rawLat.trim() === '') return null;
  if (typeof rawLon === 'string' && rawLon.trim() === '') return null;

  const lat = Number(rawLat);
  const lon = Number(rawLon);

  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    return [lat, lon];
  }

  return null;
};

/**
 * Safely format numeric coordinates for popups without risking TypeError.
 */
export const formatCoord = (val, digits = 4) => {
  if (val == null) return '--';
  const num = Number(val);
  return Number.isFinite(num) ? num.toFixed(digits) : '--';
};

/**
 * Inner Leaflet map events listener binding onMapClick via useMapEvents hook.
 */
function MapEvents({ onMapClick }) {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        const lat = e?.latlng?.lat !== undefined
          ? e.latlng.lat
          : (Array.isArray(e?.latlng) ? e.latlng[0] : (e?.lat ?? 0));
        const lon = e?.latlng?.lng !== undefined
          ? e.latlng.lng
          : (e?.latlng?.lon !== undefined ? e.latlng.lon : (Array.isArray(e?.latlng) ? e.latlng[1] : (e?.lon ?? 0)));
        onMapClick({ lat, lon });
      }
    },
  });
  return null;
}

/**
 * MarineMap — Provider-Agnostic GIS Canvas & Strict Dumb Spatial Renderer
 *
 * Implements requirements R1 and R2 for Phase 1 Tactical Marine Intelligence Console.
 * ZERO geospatial math, distance calculations, or Turf.js dependencies.
 * Coordinates are passed strictly as-is to underlying Leaflet elements.
 */
export function MarineMap({
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  minZoom = 3,
  maxZoom = 19,
  className = '',
  style = {},
  routeCoordinates = null,
  activeRoute = null,
  alternateRoute = null,
  geofencePolygons = null,
  geofences = null,
  pfzPoints = null,
  pfzFeatures = null,
  vesselPosition = null,
  startPoint = null,
  destinationPoint = null,
  tileUrl = NAVIK_MAP_STYLES.tileLayer.url,
  tileAttribution = NAVIK_MAP_STYLES.tileLayer.attribution,
  onMapClick,
  onRouteClick,
  onZoneClick,
  onPfzClick,
}) {
  // Resolve active route coordinates without computing spatial metrics
  let resolvedActiveRoute = null;
  let activeRouteColor = NAVIK_MAP_STYLES.routes.active.color;
  let activeRouteWeight = NAVIK_MAP_STYLES.routes.active.weight;

  if (Array.isArray(routeCoordinates) && routeCoordinates.length > 0) {
    resolvedActiveRoute = routeCoordinates;
  } else if (activeRoute) {
    if (Array.isArray(activeRoute) && activeRoute.length > 0) {
      resolvedActiveRoute = activeRoute;
    } else if (Array.isArray(activeRoute.coordinates) && activeRoute.coordinates.length > 0) {
      resolvedActiveRoute = activeRoute.coordinates;
      if (activeRoute.color) activeRouteColor = activeRoute.color;
      if (activeRoute.weight) activeRouteWeight = activeRoute.weight;
    }
  }

  // Resolve alternate route coordinates
  let resolvedAlternateRoute = null;
  let alternateColor = NAVIK_MAP_STYLES.routes.alternate.color;
  let alternateDash = NAVIK_MAP_STYLES.routes.alternate.dashArray;

  if (alternateRoute) {
    if (Array.isArray(alternateRoute) && alternateRoute.length > 0) {
      resolvedAlternateRoute = alternateRoute;
    } else if (Array.isArray(alternateRoute.coordinates) && alternateRoute.coordinates.length > 0) {
      resolvedAlternateRoute = alternateRoute.coordinates;
      if (alternateRoute.color) alternateColor = alternateRoute.color;
      if (alternateRoute.dashArray) alternateDash = alternateRoute.dashArray;
    }
  }

  // Resolve geofences / boundary polygons with strict array validation
  const resolvedGeofences = [];
  const rawGeofences = geofencePolygons || geofences;
  if (Array.isArray(rawGeofences)) {
    for (let i = 0; i < rawGeofences.length; i++) {
      const g = rawGeofences[i];
      if (!g) continue;
      const positions = Array.isArray(g.coordinates)
        ? g.coordinates
        : (Array.isArray(g.positions) ? g.positions : (Array.isArray(g) ? g : null));
      if (positions && positions.length > 0) {
        resolvedGeofences.push({
          id: (typeof g === 'object' && g.id) || `geofence-${i}`,
          name: typeof g === 'object' ? g.name : undefined,
          type: typeof g === 'object' ? g.type : undefined,
          positions,
          color: (typeof g === 'object' && g.color) || NAVIK_MAP_STYLES.geofences.restricted.color,
          fillColor: (typeof g === 'object' && g.fillColor) || NAVIK_MAP_STYLES.geofences.restricted.fillColor,
          fillOpacity: (typeof g === 'object' && g.fillOpacity !== undefined) ? g.fillOpacity : NAVIK_MAP_STYLES.geofences.restricted.fillOpacity,
          weight: (typeof g === 'object' && g.weight) || NAVIK_MAP_STYLES.geofences.restricted.weight,
        });
      }
    }
  }

  // Resolve PFZ points / features with defensive parseLatLng
  const resolvedPfzPoints = [];
  const rawPfz = pfzPoints || pfzFeatures;
  if (Array.isArray(rawPfz)) {
    for (let i = 0; i < rawPfz.length; i++) {
      const p = rawPfz[i];
      if (!p) continue;
      const pos = p.position ? parseLatLng(p.position) : parseLatLng(p);
      if (pos) {
        resolvedPfzPoints.push({
          id: (typeof p === 'object' && p.id) || `pfz-${pos[0]}-${pos[1]}-${i}`,
          position: pos,
          label: typeof p === 'object' ? (p.label || p.name) : undefined,
          confidence: typeof p === 'object' ? p.confidence : undefined,
          raw: p,
        });
      }
    }
  }

  // Resolve vessel position via defensive parseLatLng
  const resolvedVesselPos = parseLatLng(vesselPosition);

  // Resolve start waypoint via defensive parseLatLng
  const resolvedStartPos = parseLatLng(startPoint);

  // Resolve destination waypoint via defensive parseLatLng
  const resolvedDestPos = parseLatLng(destinationPoint);

  const wrapperStyle = {
    backgroundColor: NAVIK_MAP_STYLES.containerBackground,
    width: '100%',
    height: '100%',
    minHeight: '400px',
    ...style,
  };

  return (
    <div
      className={`marine-map-wrapper relative w-full h-full bg-[#07111F] ${className}`}
      style={wrapperStyle}
    >
      <MapContainer
        center={center}
        zoom={zoom}
        minZoom={minZoom}
        maxZoom={maxZoom}
        scrollWheelZoom={true}
        className="w-full h-full bg-[#07111F]"
        style={{ width: '100%', height: '100%', backgroundColor: NAVIK_MAP_STYLES.containerBackground }}
      >
        <MapEvents onMapClick={onMapClick} />

        <TileLayer
          url={tileUrl}
          attribution={tileAttribution}
          maxZoom={maxZoom}
          subdomains="abcd"
        />

        {/* Restricted Geofences & MPAs — Coral Red #FF5C5C */}
        {resolvedGeofences.map((geofence) => (
          <Polygon
            key={geofence.id}
            positions={geofence.positions}
            pathOptions={{
              color: geofence.color,
              fillColor: geofence.fillColor,
              fillOpacity: geofence.fillOpacity,
              weight: geofence.weight,
            }}
            eventHandlers={{
              click: () => onZoneClick && onZoneClick(geofence),
            }}
          >
            {geofence.name && (
              <Popup>
                <div className="text-xs font-sans text-slate-100 p-1">
                  <p className="font-bold text-[#FF5C5C]">{geofence.name}</p>
                  {geofence.type && (
                    <p className="text-xs text-slate-300">Type: {geofence.type}</p>
                  )}
                </div>
              </Popup>
            )}
          </Polygon>
        ))}

        {/* Alternate / Baseline Route — Slate #64748b dashed */}
        {resolvedAlternateRoute && (
          <Polyline
            positions={resolvedAlternateRoute}
            pathOptions={{
              color: alternateColor,
              weight: 2,
              dashArray: alternateDash,
              opacity: 0.8,
            }}
          />
        )}

        {/* Active Route Vector — Cyan #00D4FF */}
        {resolvedActiveRoute && (
          <Polyline
            positions={resolvedActiveRoute}
            pathOptions={{
              color: activeRouteColor,
              weight: activeRouteWeight,
              opacity: 0.95,
            }}
            eventHandlers={{
              click: () => onRouteClick && onRouteClick(activeRoute || routeCoordinates),
            }}
          />
        )}

        {/* PFZ Advisory Hotspots — Amber #FFB547 */}
        {resolvedPfzPoints.map((pfz) => (
          <Marker
            key={pfz.id}
            position={pfz.position}
            eventHandlers={{
              click: () => onPfzClick && onPfzClick(pfz.raw),
            }}
          >
            {(pfz.label || pfz.confidence !== undefined) && (
              <Popup>
                <div className="text-xs font-sans p-1">
                  {pfz.label && <p className="font-bold text-[#FFB547]">{pfz.label}</p>}
                  {typeof pfz.confidence === 'number' && Number.isFinite(pfz.confidence) && (
                    <p className="text-slate-300">
                      Confidence: {(pfz.confidence * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              </Popup>
            )}
          </Marker>
        ))}

        {/* Departure Waypoint — Sea Green #18C7A0 */}
        {resolvedStartPos && (
          <Marker position={resolvedStartPos}>
            <Popup>
              <div className="text-xs font-sans p-1">
                <p className="font-bold text-[#18C7A0]">Departure Point</p>
                <p className="text-slate-300 font-mono text-[10px]">
                  {formatCoord(resolvedStartPos[0])}, {formatCoord(resolvedStartPos[1])}
                </p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Destination Waypoint — Pure White #FFFFFF */}
        {resolvedDestPos && (
          <Marker position={resolvedDestPos}>
            <Popup>
              <div className="text-xs font-sans p-1">
                <p className="font-bold text-white">Destination Waypoint</p>
                <p className="text-slate-300 font-mono text-[10px]">
                  {formatCoord(resolvedDestPos[0])}, {formatCoord(resolvedDestPos[1])}
                </p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Vessel Telemetry Position — Cyan #00D4FF */}
        {resolvedVesselPos && (
          <Marker position={resolvedVesselPos}>
            <Popup>
              <div className="text-xs font-sans p-1">
                <p className="font-bold text-[#00D4FF]">
                  {(typeof vesselPosition === 'object' && vesselPosition?.name) || 'Current Vessel'}
                </p>
                <p className="text-slate-300 font-mono text-[10px]">
                  {formatCoord(resolvedVesselPos[0])}, {formatCoord(resolvedVesselPos[1])}
                </p>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}

export default MarineMap;
