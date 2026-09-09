import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// MapLibre creates a worker blob at module load; jsdom does not provide this
// browser URL API by default.
if (typeof window !== 'undefined') {
  window.URL.createObjectURL ||= vi.fn(() => 'blob:vitest-map-worker');
  window.URL.revokeObjectURL ||= vi.fn();
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Polyfill container layout dimensions for JSDOM
Object.defineProperties(HTMLElement.prototype, {
  clientWidth: { get: () => 1024, configurable: true },
  clientHeight: { get: () => 768, configurable: true },
  offsetWidth: { get: () => 1024, configurable: true },
  offsetHeight: { get: () => 768, configurable: true },
});

HTMLElement.prototype.getBoundingClientRect = () => ({
  top: 0,
  left: 0,
  bottom: 768,
  right: 1024,
  width: 1024,
  height: 768,
  x: 0,
  y: 0,
  toJSON: () => {},
});

// Polyfill ResizeObserver
if (typeof window !== 'undefined' && !window.ResizeObserver) {
  class MockResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.ResizeObserver = MockResizeObserver;
  global.ResizeObserver = MockResizeObserver;
}

// Polyfill SVG getBBox
if (typeof SVGElement !== 'undefined' && !SVGElement.prototype.getBBox) {
  SVGElement.prototype.getBBox = () => ({
    x: 0,
    y: 0,
    width: 100,
    height: 100,
  });
}
