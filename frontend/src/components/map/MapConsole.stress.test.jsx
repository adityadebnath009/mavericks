import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';

// Mock WebGL and DOM globals
if (typeof window !== 'undefined') {
  window.URL.createObjectURL = vi.fn();
  window.URL.revokeObjectURL = vi.fn();
}

// Mock maplibre-gl
const setPaintPropertyMock = vi.fn();
const setLayoutPropertyMock = vi.fn();
const addLayerMock = vi.fn();
const addSourceMock = vi.fn();
const getLayerMock = vi.fn();
const getSourceMock = vi.fn();

const mapMock = {
  on: vi.fn(),
  off: vi.fn(),
  remove: vi.fn(),
  addSource: addSourceMock,
  getSource: getSourceMock,
  addLayer: addLayerMock,
  getLayer: getLayerMock,
  setPaintProperty: setPaintPropertyMock,
  setLayoutProperty: setLayoutPropertyMock,
  isStyleLoaded: vi.fn().mockReturnValue(true),
  easeTo: vi.fn(),
  getCanvas: vi.fn().mockReturnValue({ style: {} }),
  addControl: vi.fn(),
  setFeatureState: vi.fn()
};

vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(() => mapMock),
    Marker: vi.fn(() => ({ setLngLat: vi.fn().mockReturnThis(), addTo: vi.fn().mockReturnThis(), remove: vi.fn(), on: vi.fn().mockReturnThis() })),
    Popup: vi.fn(() => ({ setLngLat: vi.fn().mockReturnThis(), setHTML: vi.fn().mockReturnThis(), setDOMContent: vi.fn().mockReturnThis(), addTo: vi.fn().mockReturnThis(), remove: vi.fn() })),
    NavigationControl: vi.fn()
  }
}));

import MapConsole from './MapConsole';

describe('MapConsole - Rigorous Stress Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Simulate map "load" event
    mapMock.on.mockImplementation((event, arg2) => {
      if (event === 'load' && typeof arg2 === 'function') arg2();
    });
  });

  it('Stress Test 1: Empty Arrays & Nulls (Resilience)', () => {
    // Component should not crash when fed completely empty data structures
    expect(() => {
      render(
        <MapConsole 
          activeMode="routing" 
          selectedLocation={{ lat: 15, lon: 75 }} 
          overlayLayers={[]} 
          pfzGeojson={{}}
          routeData={null}
          advisoriesGeojson={{ features: [] }}
        />
      );
    }).not.toThrow();
  });

  it('Stress Test 2: Malformed Overlay Payloads (Silent Failures)', () => {
    const malformedOverlays = [
      { id: "missing-type" }, // No type
      { id: "missing-data", type: "geojson" }, // Missing data
      { id: "missing-tiles", type: "raster" }, // Missing tiles
      null, // Literal null inside array
      undefined
    ];

    expect(() => {
      render(<MapConsole activeMode="routing" selectedLocation={{ lat: 15, lon: 75 }} overlayLayers={malformedOverlays} />);
    }).not.toThrow();
    
    // addSource should NOT be called for malformed layers
    expect(addSourceMock).not.toHaveBeenCalledWith("v2-source-missing-data", expect.anything());
    expect(addSourceMock).not.toHaveBeenCalledWith("v2-source-missing-tiles", expect.anything());
  });

  it('Stress Test 3: Dynamic Visibility Toggle (Re-render safety)', () => {
    // 1st Render: Layer doesn't exist, getLayer returns null
    getLayerMock.mockReturnValueOnce(null);
    const { rerender } = render(
      <MapConsole 
        activeMode="routing" 
        selectedLocation={{ lat: 15, lon: 75 }} 
        overlayLayers={[{ id: "test_lyr", type: "raster", tiles: ["url"], visible: true, opacity: 0.8, status: "AVAILABLE" }]} 
      />
    );

    // Filter calls to only count the dynamic layer, ignoring the 16 V1 base layers
    const dynamicAddLayerCalls = addLayerMock.mock.calls.filter(call => call[0].id === "v2-layer-test_lyr");
    expect(dynamicAddLayerCalls.length).toBe(1);

    // 2nd Render: Layer now exists, simulate user toggling visibility off
    getLayerMock.mockReturnValue({ id: "v2-layer-test_lyr" }); // Mock that layer exists now
    getSourceMock.mockReturnValue({}); // Mock that source exists
    
    addLayerMock.mockClear(); // Clear the mock counts for the next assertion
    
    rerender(
      <MapConsole 
        activeMode="routing" 
        selectedLocation={{ lat: 15, lon: 75 }} 
        overlayLayers={[{ id: "test_lyr", type: "raster", tiles: ["url"], visible: false, opacity: 0.8, status: "AVAILABLE" }]} 
      />
    );

    // It should NOT call addLayer again for this specific layer
    const dynamicAddLayerCallsAfter = addLayerMock.mock.calls.filter(call => call[0].id === "v2-layer-test_lyr");
    expect(dynamicAddLayerCallsAfter.length).toBe(0); 
    
    // It SHOULD call setPaintProperty and setLayoutProperty to hide it
    expect(setPaintPropertyMock).toHaveBeenCalledWith("v2-layer-test_lyr", "raster-opacity", 0.0);
    expect(setLayoutPropertyMock).toHaveBeenCalledWith("v2-layer-test_lyr", "visibility", "none");
  });

  it('Stress Test 4: Rapid Opacity Changes (Slider Interaction)', () => {
    getLayerMock.mockReturnValue({ id: "v2-layer-test_lyr" });
    getSourceMock.mockReturnValue({});
    
    const { rerender } = render(
      <MapConsole 
        activeMode="routing" 
        selectedLocation={{ lat: 15, lon: 75 }} 
        overlayLayers={[{ id: "test_lyr", type: "raster", tiles: ["url"], visible: true, opacity: 0.5, status: "AVAILABLE" }]} 
      />
    );

    expect(setPaintPropertyMock).toHaveBeenCalledWith("v2-layer-test_lyr", "raster-opacity", 0.5);

    // Simulate slider drag
    rerender(
      <MapConsole 
        activeMode="routing" 
        selectedLocation={{ lat: 15, lon: 75 }} 
        overlayLayers={[{ id: "test_lyr", type: "raster", tiles: ["url"], visible: true, opacity: 0.22, status: "AVAILABLE" }]} 
      />
    );

    expect(setPaintPropertyMock).toHaveBeenCalledWith("v2-layer-test_lyr", "raster-opacity", 0.22);
  });
});
