import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';

// Mock WebGL and DOM globals before anything imports maplibre
if (typeof window !== 'undefined') {
  window.URL.createObjectURL = vi.fn();
  window.URL.revokeObjectURL = vi.fn();
}

// Mock maplibregl
const getSourceMock = vi.fn();
const addSourceMock = vi.fn();
const addLayerMock = vi.fn();
const getLayerMock = vi.fn();
const setPaintPropertyMock = vi.fn();
const setFeatureStateMock = vi.fn();

const mapMock = {
  on: vi.fn(),
  off: vi.fn(),
  remove: vi.fn(),
  addSource: addSourceMock,
  getSource: getSourceMock,
  addLayer: addLayerMock,
  getLayer: getLayerMock,
  setPaintProperty: setPaintPropertyMock,
  setLayoutProperty: vi.fn(),
  isStyleLoaded: vi.fn().mockReturnValue(true),
  easeTo: vi.fn(),
  getCanvas: vi.fn().mockReturnValue({ style: {} }),
  queryRenderedFeatures: vi.fn().mockReturnValue([]),
  setFeatureState: setFeatureStateMock,
  addControl: vi.fn()
};

const markerMock = {
  setLngLat: vi.fn().mockReturnThis(),
  addTo: vi.fn().mockReturnThis(),
  remove: vi.fn(),
  on: vi.fn().mockReturnThis(),
  getLngLat: vi.fn().mockReturnValue({ lat: 15, lng: 75 })
};

vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(() => mapMock),
    Marker: vi.fn(() => markerMock),
    Popup: vi.fn(() => ({ setLngLat: vi.fn().mockReturnThis(), setHTML: vi.fn().mockReturnThis(), setDOMContent: vi.fn().mockReturnThis(), addTo: vi.fn().mockReturnThis(), remove: vi.fn() })),
    NavigationControl: vi.fn()
  }
}));

import MapConsole from './MapConsole';

describe('MapConsole - Sprint 1 & 2 Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getLayerMock.mockReturnValue(null);
    getSourceMock.mockReturnValue(null);
    
    // Simulate the map's style "load" event automatically
    mapMock.on.mockImplementation((event, arg2) => {
      if (event === 'load' && typeof arg2 === 'function') {
        arg2();
      }
    });
  });

  it('Edge Case 1: V1 Fallback (Safely renders without crashing when overlayLayers is completely missing)', () => {
    expect(() => {
      render(<MapConsole activeMode="routing" selectedLocation={{ lat: 15, lon: 75 }} />);
    }).not.toThrow();
    
    // The V1 hardcoded layers should still be added (we added them on 'load')
    expect(addLayerMock).toHaveBeenCalledWith(expect.objectContaining({ id: 'bsi-grid-fill' }));
  });

  it('Edge Case 2: V2 GEE Raster Injection (Dynamically injects raster tiles if overlayLayers provided)', () => {
    const mockOverlay = [{
      id: "gee_sst_edge",
      type: "raster",
      status: "AVAILABLE",
      visible: true,
      tiles: ["https://earthengine.googleapis.com/v1/projects/.../tiles/{z}/{x}/{y}"]
    }];

    render(<MapConsole activeMode="routing" selectedLocation={{ lat: 15, lon: 75 }} overlayLayers={mockOverlay} />);

    // Should create a source dynamically
    expect(addSourceMock).toHaveBeenCalledWith("v2-source-gee_sst_edge", {
      type: "raster",
      tiles: ["https://earthengine.googleapis.com/v1/projects/.../tiles/{z}/{x}/{y}"],
      tileSize: 256
    });

    // Should create the layer dynamically
    expect(addLayerMock).toHaveBeenCalledWith(expect.objectContaining({
      id: "v2-layer-gee_sst_edge",
      type: "raster",
      source: "v2-source-gee_sst_edge",
      paint: {
        'raster-opacity': 0.65,
        'raster-fade-duration': 300
      },
      layout: { visibility: 'visible' }
    }));
  });

  it('Edge Case 3: Honest Pipeline Rule (Refuses to render GEE layers when status is UNAVAILABLE)', () => {
    const mockOverlay = [{
      id: "gee_sst_edge",
      type: "raster",
      status: "UNAVAILABLE", // Simulated API drop / GEE timeout
      visible: true,
      tiles: ["https://earthengine.googleapis.com/v1/projects/.../tiles/{z}/{x}/{y}"]
    }];

    render(<MapConsole activeMode="routing" selectedLocation={{ lat: 15, lon: 75 }} overlayLayers={mockOverlay} />);

    // The guard clause `if (layer.status === "UNAVAILABLE") return;` should block this
    expect(addSourceMock).not.toHaveBeenCalledWith("v2-source-gee_sst_edge", expect.anything());
    expect(addLayerMock).not.toHaveBeenCalledWith(expect.objectContaining({ id: "v2-layer-gee_sst_edge" }));
  });
});
