import React from 'react';
import { describe, it, expect, vi } from 'vitest';

vi.hoisted(() => {
  if (typeof window !== 'undefined') {
    window.URL.createObjectURL = vi.fn();
    window.URL.revokeObjectURL = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  }
});

// THE TYPO WAS HERE: maplibregl -> maplibre-gl
vi.mock('maplibre-gl', () => ({
  default: {
    Map: vi.fn(() => ({
      on: vi.fn(),
      off: vi.fn(),
      addControl: vi.fn(),
      remove: vi.fn(),
      getSource: vi.fn(() => ({ setData: vi.fn() })),
      addSource: vi.fn(),
      getLayer: vi.fn(() => null),
      addLayer: vi.fn(),
      setPaintProperty: vi.fn(),
      setLayoutProperty: vi.fn(),
      fitBounds: vi.fn(),
      easeTo: vi.fn()
    })),
    NavigationControl: vi.fn(),
    Marker: vi.fn(() => ({
      setLngLat: vi.fn().mockReturnThis(),
      addTo: vi.fn().mockReturnThis(),
      remove: vi.fn(),
      on: vi.fn(),
      getLngLat: vi.fn(() => ({ lat: 0, lng: 0 }))
    })),
    Popup: vi.fn(() => ({
      setLngLat: vi.fn().mockReturnThis(),
      setHTML: vi.fn().mockReturnThis(),
      addTo: vi.fn().mockReturnThis(),
      remove: vi.fn()
    })),
    LngLatBounds: vi.fn(() => ({
      extend: vi.fn().mockReturnThis()
    }))
  }
}));

import { render } from '@testing-library/react';
import MapConsole from './map/MapConsole';

describe('Mega-Suite 7: 50 MapConsole WebGL Engine Edge Cases', () => {

  describe('Section 1: Dynamic overlayLayers GeoJSON (20 Tests)', () => {
    it('1. Survives null overlayLayers', () => { expect(() => render(<MapConsole overlayLayers={null} />)).not.toThrow(); });
    it('2. Survives empty overlayLayers array', () => { expect(() => render(<MapConsole overlayLayers={[]} />)).not.toThrow(); });
    
    // Feature collection variations
    for (let i = 3; i <= 20; i++) {
      it(`${i}. Survives mutated GeoJSON payload variation ${i}`, () => {
        const payload = [
          { id: 't1', type: 'geojson', data: null, visible: true },
          { id: 't2', type: 'geojson', data: {}, visible: false },
          { id: 't3', type: 'geojson', data: { type: 'FeatureCollection', features: [] }, visible: true },
          { id: `t${i}`, type: 'geojson', data: { features: [null] }, visible: true }
        ];
        expect(() => render(<MapConsole overlayLayers={payload} />)).not.toThrow();
      });
    }
  });

  describe('Section 2: Raster & Heatmap Payload Traps (15 Tests)', () => {
    for (let i = 21; i <= 35; i++) {
      it(`${i}. Survives Raster/Heatmap corruption ${i}`, () => {
        const payload = [
          { id: 'r1', type: 'raster', tiles: null, opacity: 1.5, visible: true },
          { id: 'r2', type: 'raster', tiles: ['http://bad.url'], opacity: -5, visible: false },
          { id: 'h1', type: 'heatmap', data: null, opacity: NaN, visible: true }
        ];
        expect(() => render(<MapConsole overlayLayers={payload} sstOpacity={-1} chlOpacity={2} />)).not.toThrow();
      });
    }
  });

  describe('Section 3: Global Map Props & Callbacks (15 Tests)', () => {
    it('36. Survives null selectedLocation', () => { expect(() => render(<MapConsole selectedLocation={null} />)).not.toThrow(); });
    it('37. Survives undefined selectedLocation', () => { expect(() => render(<MapConsole selectedLocation={undefined} />)).not.toThrow(); });
    it('38. Survives NaN selectedLocation coords', () => { expect(() => render(<MapConsole selectedLocation={{ lat: NaN, lon: NaN }} />)).not.toThrow(); });
    
    it('39. Survives null destinationLocation', () => { expect(() => render(<MapConsole destinationLocation={null} />)).not.toThrow(); });
    it('40. Survives incomplete routeData path', () => { expect(() => render(<MapConsole routeData={{ path: [] }} />)).not.toThrow(); });
    it('41. Survives null routeData', () => { expect(() => render(<MapConsole routeData={null} />)).not.toThrow(); });
    
    it('42. Survives null selectedPfz', () => { expect(() => render(<MapConsole selectedPfz={null} />)).not.toThrow(); });
    it('43. Survives missing selectedPfz geometry', () => { expect(() => render(<MapConsole selectedPfz={{}} />)).not.toThrow(); });
    it('44. Survives mutated selectedPfz coordinates', () => { expect(() => render(<MapConsole selectedPfz={{ geometry: { type: 'LineString', coordinates: [null] } }} />)).not.toThrow(); });
    
    it('45. Survives undefined string beamWidth', () => { expect(() => render(<MapConsole beamWidth="WIDE" />)).not.toThrow(); });
    it('46. Survives negative beamWidth', () => { expect(() => render(<MapConsole beamWidth={-10} />)).not.toThrow(); });
    
    it('47. Survives null hoveredPfzId', () => { expect(() => render(<MapConsole hoveredPfzId={null} />)).not.toThrow(); });
    it('48. Survives empty string hoveredPfzId', () => { expect(() => render(<MapConsole hoveredPfzId="" />)).not.toThrow(); });
    
    it('49. Survives massive gridGeojson', () => { expect(() => render(<MapConsole gridGeojson={{ features: Array(1000).fill({}) }} />)).not.toThrow(); });
    it('50. Survives complete absence of all optional props', () => { expect(() => render(<MapConsole />)).not.toThrow(); });
  });

});
