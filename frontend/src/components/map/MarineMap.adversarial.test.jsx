import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock react-leaflet with semantic test primitives
vi.mock('react-leaflet', async () => {
  return await import('../../test/mocks/reactLeafletMock');
});

import { MarineMap } from './MarineMap';

describe('Adversarial Stress Harness for MarineMap', () => {

  describe('Vector 1: Empty Coordinate Arrays', () => {
    it('handles startPoint as empty array without crashing', () => {
      expect(() => {
        render(<MarineMap startPoint={[]} />);
      }).not.toThrow();
    });

    it('handles destinationPoint as empty array without crashing', () => {
      expect(() => {
        render(<MarineMap destinationPoint={[]} />);
      }).not.toThrow();
    });

    it('handles vesselPosition as empty array without crashing', () => {
      expect(() => {
        render(<MarineMap vesselPosition={[]} />);
      }).not.toThrow();
    });

    it('handles routeCoordinates as empty array', () => {
      expect(() => {
        render(<MarineMap routeCoordinates={[]} />);
      }).not.toThrow();
      expect(screen.queryByTestId('map-polyline')).not.toBeInTheDocument();
    });

    it('handles activeRoute as empty array or empty coordinates', () => {
      expect(() => {
        render(<MarineMap activeRoute={[]} />);
        render(<MarineMap activeRoute={{ coordinates: [] }} />);
      }).not.toThrow();
    });

    it('handles pfzPoints as empty array', () => {
      expect(() => {
        render(<MarineMap pfzPoints={[]} />);
      }).not.toThrow();
      expect(screen.queryByTestId('map-marker')).not.toBeInTheDocument();
    });

    it('handles geofences as empty array', () => {
      expect(() => {
        render(<MarineMap geofences={[]} />);
      }).not.toThrow();
      expect(screen.queryByTestId('map-polygon')).not.toBeInTheDocument();
    });
  });

  describe('Vector 2: Single-Point and Truncated Coordinates', () => {
    it('handles startPoint with only one coordinate [15.0] without crashing', () => {
      expect(() => {
        render(<MarineMap startPoint={[15.0]} />);
      }).not.toThrow();
    });

    it('handles destinationPoint with only one coordinate [16.0] without crashing', () => {
      expect(() => {
        render(<MarineMap destinationPoint={[16.0]} />);
      }).not.toThrow();
    });

    it('handles vesselPosition with only one coordinate [15.5] without crashing', () => {
      expect(() => {
        render(<MarineMap vesselPosition={[15.5]} />);
      }).not.toThrow();
    });

    it('handles single-point route polyline [[15.0, 75.0]]', () => {
      expect(() => {
        render(<MarineMap routeCoordinates={[[15.0, 75.0]]} />);
      }).not.toThrow();
    });
  });

  describe('Vector 3: Non-Standard Coordinate Types (Strings & Numerics)', () => {
    it('handles string coordinates in startPoint ["15.0", "75.0"] without crashing', () => {
      expect(() => {
        render(<MarineMap startPoint={["15.0", "75.0"]} />);
      }).not.toThrow();
    });

    it('handles string coordinates in destinationPoint ["16.0", "76.0"] without crashing', () => {
      expect(() => {
        render(<MarineMap destinationPoint={["16.0", "76.0"]} />);
      }).not.toThrow();
    });

    it('handles string coordinates in vesselPosition { lat: "15.0", lon: "75.0" } without crashing', () => {
      expect(() => {
        render(<MarineMap vesselPosition={{ lat: "15.0", lon: "75.0" }} />);
      }).not.toThrow();
    });

    it('handles string coordinates in routeCoordinates [["15.0", "75.0"], ["16.0", "76.0"]]', () => {
      expect(() => {
        render(<MarineMap routeCoordinates={[["15.0", "75.0"], ["16.0", "76.0"]]} />);
      }).not.toThrow();
    });
  });

  describe('Vector 4: Malformed Geofences & PFZ Features', () => {
    it('handles geofence with string coordinates without propagating invalid positions', () => {
      expect(() => {
        render(<MarineMap geofencePolygons={[{ id: 'bad-1', coordinates: "not-an-array" }]} />);
      }).not.toThrow();
      const polygon = screen.queryByTestId('map-polygon');
      if (polygon) {
        const pos = JSON.parse(polygon.getAttribute('data-positions'));
        expect(Array.isArray(pos)).toBe(true);
      }
    });

    it('handles geofence with empty sub-arrays [[]]', () => {
      expect(() => {
        render(<MarineMap geofencePolygons={[{ id: 'empty-ring', coordinates: [[]] }]} />);
      }).not.toThrow();
    });

    it('handles pfz feature with non-numeric confidence or null confidence', () => {
      expect(() => {
        render(
          <MarineMap
            pfzPoints={[
              { id: 'p1', position: [15.0, 75.0], confidence: null },
              { id: 'p2', position: [15.1, 75.1], confidence: 'high' },
              { id: 'p3', position: [15.2, 75.2], confidence: undefined },
            ]}
          />
        );
      }).not.toThrow();
    });
  });

  describe('Vector 5: Rapid Prop Mutations & Re-renders', () => {
    it('survives rapid consecutive updates across all prop dimensions', () => {
      const { rerender } = render(<MarineMap />);

      for (let i = 0; i < 50; i++) {
        rerender(
          <MarineMap
            center={[15.0 + i * 0.01, 75.0 + i * 0.01]}
            zoom={5 + (i % 5)}
            routeCoordinates={[
              [15.0, 75.0],
              [15.0 + i * 0.01, 75.0 + i * 0.01],
            ]}
            vesselPosition={[15.0 + i * 0.01, 75.0 + i * 0.01]}
            startPoint={[15.0, 75.0]}
            destinationPoint={[16.0, 76.0]}
          />
        );
      }
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });
  });

  describe('Vector 6: Strict Zero Math Enforcement During Rendering', () => {
    it('executes zero trigonometric or distance calculations across adversarial props', () => {
      const mathSpies = [
        vi.spyOn(Math, 'sin'),
        vi.spyOn(Math, 'cos'),
        vi.spyOn(Math, 'tan'),
        vi.spyOn(Math, 'asin'),
        vi.spyOn(Math, 'acos'),
        vi.spyOn(Math, 'atan'),
        vi.spyOn(Math, 'atan2'),
        vi.spyOn(Math, 'sqrt'),
        vi.spyOn(Math, 'hypot'),
      ];

      render(
        <MarineMap
          center={[15.0, 75.0]}
          routeCoordinates={[
            [15.0, 75.0],
            [15.2, 75.2],
            [15.5, 75.8],
          ]}
          vesselPosition={[15.2, 75.2]}
          startPoint={[15.0, 75.0]}
          destinationPoint={[15.5, 75.8]}
          geofencePolygons={[
            {
              id: 'g1',
              coordinates: [
                [14.0, 74.0],
                [14.5, 74.0],
                [14.5, 74.5],
                [14.0, 74.5],
              ],
            },
          ]}
          pfzPoints={[
            { id: 'pfz1', position: [15.1, 75.1], confidence: 0.85 },
          ]}
        />
      );

      mathSpies.forEach(spy => {
        expect(spy).not.toHaveBeenCalled();
        spy.mockRestore();
      });
    });
  });
});
