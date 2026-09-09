import React from 'react';
import { vi } from 'vitest';

export const MapContainer = ({ children, center, zoom, minZoom, maxZoom, className, style, ...props }) => (
  <div
    data-testid="map-container"
    data-center={JSON.stringify(center)}
    data-zoom={zoom}
    data-minzoom={minZoom}
    data-maxzoom={maxZoom}
    className={className}
    style={style}
    {...props}
  >
    {children}
  </div>
);

export const TileLayer = ({ url, attribution, ...props }) => (
  <div
    data-testid="tile-layer"
    data-url={url}
    data-attribution={attribution}
    {...props}
  />
);

export const Marker = ({ position, children, icon, ...props }) => (
  <div
    data-testid="map-marker"
    data-position={JSON.stringify(position)}
    data-icon={icon ? 'custom-icon' : undefined}
    {...props}
  >
    {children}
  </div>
);

export const CircleMarker = ({ center, radius, pathOptions, children, ...props }) => (
  <div
    data-testid="map-circle-marker"
    data-center={JSON.stringify(center)}
    data-radius={radius}
    data-color={pathOptions?.color}
    data-fillcolor={pathOptions?.fillColor}
    data-pathoptions={JSON.stringify(pathOptions)}
    {...props}
  >
    {children}
  </div>
);

export const Polyline = ({ positions, pathOptions, ...props }) => (
  <div
    data-testid="map-polyline"
    data-positions={JSON.stringify(positions)}
    data-color={pathOptions?.color}
    data-weight={pathOptions?.weight}
    data-dasharray={pathOptions?.dashArray}
    data-pathoptions={JSON.stringify(pathOptions)}
    {...props}
  />
);

export const Polygon = ({ positions, pathOptions, ...props }) => (
  <div
    data-testid="map-polygon"
    data-positions={JSON.stringify(positions)}
    data-color={pathOptions?.color}
    data-fillcolor={pathOptions?.fillColor}
    data-pathoptions={JSON.stringify(pathOptions)}
    {...props}
  />
);

export const Popup = ({ children, ...props }) => (
  <div data-testid="map-popup" {...props}>
    {children}
  </div>
);

export const Tooltip = ({ children, ...props }) => (
  <div data-testid="map-tooltip" {...props}>
    {children}
  </div>
);

export const useMap = () => ({
  setView: vi.fn(),
  flyTo: vi.fn(),
  panTo: vi.fn(),
  fitBounds: vi.fn(),
  getSize: () => ({ x: 1024, y: 768 }),
  on: vi.fn(),
  off: vi.fn(),
});

export const useMapEvents = (handlers = {}) => {
  React.useEffect(() => {
    const handleContainerClick = (e) => {
      if (handlers && typeof handlers.click === 'function') {
        const lat = e?.detail?.lat ?? e?.lat ?? 15.0;
        const lng = e?.detail?.lon ?? e?.detail?.lng ?? e?.lon ?? e?.lng ?? 75.0;
        handlers.click({
          latlng: { lat, lng },
          originalEvent: e,
        });
      }
    };
    const container = document.querySelector('[data-testid="map-container"]');
    if (container) {
      container.addEventListener('click', handleContainerClick);
      return () => container.removeEventListener('click', handleContainerClick);
    }
  }, [handlers]);
  return handlers;
};

export default {
  MapContainer,
  TileLayer,
  Marker,
  CircleMarker,
  Polyline,
  Polygon,
  Popup,
  Tooltip,
  useMap,
  useMapEvents,
};
