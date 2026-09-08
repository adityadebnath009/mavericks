import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import fs from 'fs';
import path from 'path';

// Mock react-leaflet with semantic test primitives
vi.mock('react-leaflet', async () => {
  return await import('../../test/mocks/reactLeafletMock');
});

// Import component under test
import { MarineMap, NAVIK_MAP_STYLES, parseLatLng, formatCoord } from './MarineMap';

describe('MarineMap — Tactical Marine Intelligence GIS Canvas', () => {
  const defaultCenter = [15.0, 75.0];
  const defaultZoom = 6;

  const mockPfzPoints = [
    { id: 'pfz-1', position: [13.0827, 80.2707], label: 'Chennai Offshore Sector', confidence: 0.88 },
    { id: 'pfz-2', position: [14.1200, 81.5400], label: 'Nellore Swell Boundary', confidence: 0.92 },
  ];

  const mockRoute = [
    [15.0, 75.0],
    [15.2, 75.4],
    [15.6, 75.9],
  ];

  const mockGeofences = [
    {
      id: 'mpa-1',
      name: 'Gulf of Mannar Biosphere',
      coordinates: [
        [9.0, 78.5],
        [9.5, 78.5],
        [9.5, 79.2],
        [9.0, 79.2],
      ],
      type: 'restricted',
    },
  ];

  describe('Suite 1: Mounting & Baseline Configuration', () => {
    it('renders the map container with default coordinates and zoom', () => {
      render(<MarineMap />);
      const container = screen.getByTestId('map-container');
      expect(container).toBeInTheDocument();
      expect(container).toHaveAttribute('data-center', JSON.stringify(defaultCenter));
      expect(container).toHaveAttribute('data-zoom', String(defaultZoom));
    });

    it('renders with custom center and zoom when passed as props', () => {
      const customCenter = [10.0, 72.0];
      const customZoom = 8;
      render(<MarineMap center={customCenter} zoom={customZoom} />);
      const container = screen.getByTestId('map-container');
      expect(container).toHaveAttribute('data-center', JSON.stringify(customCenter));
      expect(container).toHaveAttribute('data-zoom', '8');
    });

    it('renders dark-themed base tile layer matching Deep Navy constraints', () => {
      render(<MarineMap />);
      const tileLayer = screen.getByTestId('tile-layer');
      expect(tileLayer).toBeInTheDocument();
      const url = tileLayer.getAttribute('data-url');
      expect(url).toContain('dark_all');
    });

    it('applies Navik Deep Navy (#07111F) canvas background style and class', () => {
      render(<MarineMap />);
      const container = screen.getByTestId('map-container');
      const style = container.getAttribute('style') || '';
      const className = container.getAttribute('class') || '';
      const hasDeepNavy =
        style.includes('#07111F') ||
        style.includes('rgb(7, 17, 31)') ||
        className.includes('#07111F');
      expect(hasDeepNavy).toBe(true);
    });

    it('binds map click events via useMapEvents and invokes onMapClick callback', () => {
      const onMapClick = vi.fn();
      render(<MarineMap onMapClick={onMapClick} />);
      const container = screen.getByTestId('map-container');
      container.click();
      expect(onMapClick).toHaveBeenCalledWith({ lat: 15.0, lon: 75.0 });
    });
  });

  describe('Suite 2: Spatial Props Reception & Propagation', () => {
    it('renders PFZ markers at exact incoming coordinates', () => {
      render(<MarineMap pfzPoints={mockPfzPoints} />);
      const markers = screen.getAllByTestId('map-marker');
      expect(markers).toHaveLength(2);
      expect(markers[0]).toHaveAttribute('data-position', JSON.stringify([13.0827, 80.2707]));
      expect(markers[1]).toHaveAttribute('data-position', JSON.stringify([14.1200, 81.5400]));
    });

    it('renders route polyline with exact coordinate array', () => {
      render(<MarineMap routeCoordinates={mockRoute} />);
      const polyline = screen.getByTestId('map-polyline');
      expect(polyline).toBeInTheDocument();
      expect(polyline).toHaveAttribute('data-positions', JSON.stringify(mockRoute));
    });

    it('renders activeRoute object format with custom coordinates', () => {
      const routeObject = {
        coordinates: [
          [16.0, 73.0],
          [16.5, 73.5],
        ],
        color: '#00D4FF',
        weight: 4,
      };
      render(<MarineMap activeRoute={routeObject} />);
      const polyline = screen.getByTestId('map-polyline');
      expect(polyline).toBeInTheDocument();
      expect(polyline).toHaveAttribute('data-positions', JSON.stringify(routeObject.coordinates));
    });

    it('renders alternate route polyline with dash array', () => {
      const alternateRoute = [
        [15.0, 75.0],
        [16.0, 76.0],
      ];
      render(<MarineMap alternateRoute={alternateRoute} />);
      const polyline = screen.getByTestId('map-polyline');
      expect(polyline).toBeInTheDocument();
      expect(polyline).toHaveAttribute('data-positions', JSON.stringify(alternateRoute));
      expect(polyline).toHaveAttribute('data-dasharray', '5, 5');
    });

    it('renders geofence polygons with boundary coordinates', () => {
      render(<MarineMap geofencePolygons={mockGeofences} />);
      const polygons = screen.getAllByTestId('map-polygon');
      expect(polygons).toHaveLength(1);
      expect(polygons[0]).toHaveAttribute('data-positions', JSON.stringify(mockGeofences[0].coordinates));
    });

    it('renders vessel, start, and destination waypoint markers', () => {
      render(
        <MarineMap
          vesselPosition={[15.1, 75.1]}
          startPoint={[15.0, 75.0]}
          destinationPoint={[15.6, 75.9]}
        />
      );
      const markers = screen.getAllByTestId('map-marker');
      expect(markers).toHaveLength(3);
      expect(markers[0]).toHaveAttribute('data-position', JSON.stringify([15.0, 75.0]));
      expect(markers[1]).toHaveAttribute('data-position', JSON.stringify([15.6, 75.9]));
      expect(markers[2]).toHaveAttribute('data-position', JSON.stringify([15.1, 75.1]));
    });

    it('gracefully handles empty or null spatial props without throwing', () => {
      expect(() => {
        render(
          <MarineMap
            pfzPoints={[]}
            routeCoordinates={null}
            activeRoute={null}
            alternateRoute={null}
            geofencePolygons={undefined}
            vesselPosition={null}
            startPoint={null}
            destinationPoint={null}
          />
        );
      }).not.toThrow();
      expect(screen.queryByTestId('map-marker')).not.toBeInTheDocument();
      expect(screen.queryByTestId('map-polyline')).not.toBeInTheDocument();
      expect(screen.queryByTestId('map-polygon')).not.toBeInTheDocument();
    });
  });

  describe('Suite 3: Frozen Navik Design System Conformance', () => {
    it('renders active route polyline with Cyan (#00D4FF) accent', () => {
      render(<MarineMap routeCoordinates={mockRoute} />);
      const polyline = screen.getByTestId('map-polyline');
      expect(polyline).toHaveAttribute('data-color', '#00D4FF');
      expect(polyline).toHaveAttribute('data-weight', '4');
    });

    it('renders restricted geofence polygon with Coral Red (#FF5C5C) boundary and fill', () => {
      render(<MarineMap geofencePolygons={mockGeofences} />);
      const polygon = screen.getByTestId('map-polygon');
      expect(polygon).toHaveAttribute('data-color', '#FF5C5C');
      expect(polygon).toHaveAttribute('data-fillcolor', '#FF5C5C');
    });

    it('exports NAVIK_MAP_STYLES palette constants with official hex values', () => {
      expect(NAVIK_MAP_STYLES.containerBackground).toBe('#07111F');
      expect(NAVIK_MAP_STYLES.routes.active.color).toBe('#00D4FF');
      expect(NAVIK_MAP_STYLES.geofences.restricted.color).toBe('#FF5C5C');
      expect(NAVIK_MAP_STYLES.markers.start.color).toBe('#18C7A0');
      expect(NAVIK_MAP_STYLES.markers.pfz.color).toBe('#FFB547');
      expect(NAVIK_MAP_STYLES.markers.destination.color).toBe('#FFFFFF');
    });
  });

  describe('Suite 4: Strict Dumb Renderer Verification (Zero Geospatial Math)', () => {
    it('passes high-precision coordinate floats via strict passthrough without modification', () => {
      const highPrecisionPoints = [
        [12.12345678, 80.87654321],
        [13.98765432, 81.23456789],
      ];
      render(<MarineMap routeCoordinates={highPrecisionPoints} />);
      const polyline = screen.getByTestId('map-polyline');
      const renderedPositions = JSON.parse(polyline.getAttribute('data-positions'));
      expect(renderedPositions).toEqual(highPrecisionPoints);
    });

    it('does not invoke trigonometric distance calculations during render', () => {
      const sinSpy = vi.spyOn(Math, 'sin');
      const cosSpy = vi.spyOn(Math, 'cos');
      const atan2Spy = vi.spyOn(Math, 'atan2');
      const sqrtSpy = vi.spyOn(Math, 'sqrt');

      render(
        <MarineMap
          pfzPoints={mockPfzPoints}
          routeCoordinates={mockRoute}
          geofencePolygons={mockGeofences}
          vesselPosition={[15.1, 75.1]}
          startPoint={[15.0, 75.0]}
          destinationPoint={[15.6, 75.9]}
        />
      );

      // In a pure dumb renderer, rendering coordinates must not execute spherical trigonometry
      expect(sinSpy).not.toHaveBeenCalled();
      expect(cosSpy).not.toHaveBeenCalled();
      expect(atan2Spy).not.toHaveBeenCalled();
      expect(sqrtSpy).not.toHaveBeenCalled();

      sinSpy.mockRestore();
      cosSpy.mockRestore();
      atan2Spy.mockRestore();
      sqrtSpy.mockRestore();
    });

    it('contains ZERO geospatial math library imports in source code (Static Analysis)', () => {
      const componentPath = path.resolve(__dirname, './MarineMap.jsx');
      const sourceCode = fs.readFileSync(componentPath, 'utf8');

      // Assert no geospatial calculation libraries
      expect(sourceCode).not.toMatch(/@turf/);
      expect(sourceCode).not.toMatch(/from\s+['"]turf['"]/);
      expect(sourceCode).not.toMatch(/from\s+['"]geolib['"]/);
      expect(sourceCode).not.toMatch(/from\s+['"]proj4['"]/);
      expect(sourceCode).not.toMatch(/from\s+['"]leaflet-geometryutil['"]/);
      expect(sourceCode).not.toMatch(/from\s+['"]mathjs['"]/);

      // Assert no distance or bearing calculation formula definitions
      expect(sourceCode).not.toMatch(/function\s+haversine/i);
      expect(sourceCode).not.toMatch(/function\s+calculateDistance/i);
      expect(sourceCode).not.toMatch(/function\s+getBearing/i);
      expect(sourceCode).not.toMatch(/function\s+distanceTo/i);
    });
  });
});
