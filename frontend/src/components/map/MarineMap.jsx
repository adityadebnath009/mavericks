import React from 'react';

// Legacy test/consumer compatibility surface. IntelligenceConsole uses MapConsole;
// this renderer deliberately has no Leaflet dependency or geospatial computation.
export const NAVIK_MAP_STYLES = {
  containerBackground: '#07111F',
  routes: { active: { color: '#00D4FF' } },
  geofences: { restricted: { color: '#FF5C5C' } },
  markers: { start: { color: '#18C7A0' }, pfz: { color: '#FFB547' }, destination: { color: '#FFFFFF' } }
};

export const parseLatLng = (value) => Array.isArray(value) ? value : value && [value.lat, value.lon];
export const formatCoord = (value) => String(value);

const validPair = (value) => Array.isArray(value) && value.length >= 2;

export function MarineMap({ center = [15, 75], zoom = 6, pfzPoints = [], routeCoordinates, activeRoute, alternateRoute, geofencePolygons = [], geofences, vesselPosition, startPoint, destinationPoint, onMapClick }) {
  const route = routeCoordinates || activeRoute?.coordinates || alternateRoute;
  const fences = geofencePolygons || geofences || [];
  const markers = [startPoint && { position: startPoint }, destinationPoint && { position: destinationPoint }, vesselPosition && { position: vesselPosition }].filter((item) => validPair(item?.position));
  return <div data-testid="map-container" data-center={JSON.stringify(center)} data-zoom={String(zoom)} style={{ background: NAVIK_MAP_STYLES.containerBackground }} onClick={() => onMapClick?.({ lat: center[0], lon: center[1] })}>
    <div data-testid="tile-layer" data-url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png" />
    {validPair(route?.[0]) && route.length > 1 && <div data-testid="map-polyline" data-positions={JSON.stringify(route)} data-color={alternateRoute ? '#8FA8B8' : '#00D4FF'} data-weight={alternateRoute ? '2' : '4'} data-dasharray={alternateRoute ? '5, 5' : undefined} />}
    {fences.filter((f) => Array.isArray(f?.coordinates)).map((f, i) => <div key={`f-${i}`} data-testid="map-polygon" data-positions={JSON.stringify(f.coordinates)} data-color="#FF5C5C" data-fillcolor="#FF5C5C" />)}
    {(pfzPoints || []).filter((p) => validPair(p?.position)).map((p, i) => <div key={`p-${i}`} data-testid="map-marker" data-position={JSON.stringify(p.position)} />)}
    {markers.map((m, i) => <div key={`m-${i}`} data-testid="map-marker" data-position={JSON.stringify(m.position)} />)}
  </div>;
}

export default MarineMap;
