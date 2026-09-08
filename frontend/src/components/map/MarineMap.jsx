import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Polygon, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

/**
 * Frozen Navik Design System Map Palette Constants
 */
export const NAVIK_MAP_STYLES = {
  containerBackground: '#07111F', // Deep Navy base surface
  tileLayer: {
    // Esri World Dark Gray Base (No API Key required, extremely reliable, perfectly matches our dark theme)
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
    maxZoom: 16,
  },
  routes: {
    active: {
      color: '#00D4FF', // Cyan primary accent
      weight: 4,
      opacity: 0.95,
      lineCap: 'round',
      lineJoin: 'round',
    }
  },
  geofences: {
    restricted: {
      color: '#FF5C5C', // Coral Red
      fillColor: '#FF5C5C',
      fillOpacity: 0.25,
      weight: 2,
      dashArray: '4, 4',
    }
  }
};

// Defensive coordinate parsing (from the teamwork swarm)
const parseLatLng = (coord) => {
  if (!coord) return null;
  if (Array.isArray(coord) && coord.length === 2) {
    const [lat, lng] = coord.map(Number);
    if (!isNaN(lat) && !isNaN(lng)) return [lat, lng];
  }
  if (typeof coord === 'object' && coord !== null) {
    const lat = Number(coord.lat !== undefined ? coord.lat : coord.latitude);
    const lng = Number(coord.lng !== undefined ? coord.lng : coord.lon !== undefined ? coord.lon : coord.longitude);
    if (!isNaN(lat) && !isNaN(lng)) return [lat, lng];
  }
  return null;
};

const formatCoord = (val) => Number(val).toFixed(4);

// MapEvents component for click handling
function MapEvents({ onMapClick }) {
  useMapEvents({
    click(e) {
      if (onMapClick) onMapClick([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

const MarineMap = ({
  center = [17.431, 84.703], // Default Bay of Bengal
  zoom = 6,
  activeRoute = null,
  geofencePolygons = [],
  pfzPoints = [],
  startPoint = null,
  destinationPoint = null,
  overlayLayers = [], // Google Earth Engine dynamic raster tiles
  onMapClick,
  className = '',
  style = {},
}) => {
  
  const resolvedActiveRoute = Array.isArray(activeRoute) ? activeRoute : null;
  const resolvedStartPos = parseLatLng(startPoint);
  const resolvedDestPos = parseLatLng(destinationPoint);

  return (
    <div className={`marine-map-wrapper relative w-full h-full bg-[#07111F] ${className}`} style={{ width: '100%', height: '100%', ...style }}>
      <MapContainer
        center={center}
        zoom={zoom}
        zoomControl={false} // Hide default zoom controls to keep UI clean
        scrollWheelZoom={true}
        className="w-full h-full bg-[#07111F]"
        style={{ width: '100%', height: '100%' }}
      >
        <MapEvents onMapClick={onMapClick} />

        {/* 1. Base Map (Esri Dark Gray - No Watermarks) */}
        <TileLayer
          url={NAVIK_MAP_STYLES.tileLayer.url}
          attribution={NAVIK_MAP_STYLES.tileLayer.attribution}
          maxZoom={NAVIK_MAP_STYLES.tileLayer.maxZoom}
        />

        {/* 2. Google Earth Engine Dynamic Overlays (SST, Chlorophyll, Wave Height) */}
        {overlayLayers.map((layerUrl, idx) => (
          <TileLayer
            key={`gee-overlay-${idx}`}
            url={layerUrl}
            opacity={0.65} // Translucent so base map features bleed through
            maxZoom={19}
            zIndex={10} // Ensure it renders above base but below routes
          />
        ))}

        {/* 3. Geofences / MPAs */}
        {geofencePolygons.map((geofence, idx) => (
          <Polygon
            key={`geo-${idx}`}
            positions={geofence.positions}
            pathOptions={{
              color: NAVIK_MAP_STYLES.geofences.restricted.color,
              fillColor: NAVIK_MAP_STYLES.geofences.restricted.fillColor,
              fillOpacity: NAVIK_MAP_STYLES.geofences.restricted.fillOpacity,
              weight: NAVIK_MAP_STYLES.geofences.restricted.weight,
              dashArray: NAVIK_MAP_STYLES.geofences.restricted.dashArray
            }}
          />
        ))}

        {/* 4. Active Tactical Route */}
        {resolvedActiveRoute && (
          <Polyline
            positions={resolvedActiveRoute}
            pathOptions={{
              color: NAVIK_MAP_STYLES.routes.active.color,
              weight: NAVIK_MAP_STYLES.routes.active.weight,
              opacity: NAVIK_MAP_STYLES.routes.active.opacity,
              className: 'route-pulse-animation' // Add CSS glow effect
            }}
          />
        )}

        {/* 5. PFZ Hotspots */}
        {pfzPoints.map((pfz, idx) => {
          const pos = parseLatLng(pfz.position);
          if (!pos) return null;
          return (
            <Marker key={`pfz-${idx}`} position={pos}>
              <Popup>
                <div className="text-xs font-sans p-1">
                  <p className="font-bold text-[#FFB547]">{pfz.label || 'PFZ Hotspot'}</p>
                  <p className="text-slate-300 font-mono text-[10px]">
                    {formatCoord(pos[0])}, {formatCoord(pos[1])}
                  </p>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Start / Dest Markers */}
        {resolvedStartPos && (
          <Marker position={resolvedStartPos}>
            <Popup><div className="font-bold text-[#18C7A0]">Departure Point</div></Popup>
          </Marker>
        )}
        {resolvedDestPos && (
          <Marker position={resolvedDestPos}>
            <Popup><div className="font-bold text-white">Destination Point</div></Popup>
          </Marker>
        )}

      </MapContainer>
    </div>
  );
};

export default MarineMap;
