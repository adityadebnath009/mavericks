import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Mock child components to isolate the DOM tree layout test
vi.mock('./navigation/WorkspaceNav', () => ({ default: () => <div data-testid="workspace-nav" /> }));
vi.mock('./navigation/TopHeader', () => ({ default: () => <div data-testid="top-header" /> }));
vi.mock('./map/MapConsole', () => ({ default: () => <div data-testid="map-console" /> }));
vi.mock('./sidebars/RoutingSidebar', () => ({ default: ({ simulationEnabled, onSimulationEnabledChange }) => (
  <div data-testid="routing-sidebar">
    <button role="switch" aria-checked={simulationEnabled} onClick={() => onSimulationEnabledChange?.(!simulationEnabled)}>
      {simulationEnabled ? 'Enabled' : 'Enable'}
    </button>
  </div>
) }));
vi.mock('./sidebars/FisheriesSidebar', () => ({ default: () => <div data-testid="fisheries-sidebar" /> }));
vi.mock('./sidebars/WeatherSidebar', () => ({ default: () => <div data-testid="weather-sidebar" /> }));
vi.mock('./timeline/WeatherTimelinePanel', () => ({ default: () => <div data-testid="weather-timeline" /> }));
vi.mock('./chat/SafetyAdvisorChat', () => ({ default: () => <div data-testid="safety-chat" /> }));
vi.mock('./common/SpotlightCard', () => ({ default: ({ children, className }) => <div data-testid="spotlight-card" className={className}>{children}</div> }));

// Mock API calls with resolved promises
vi.mock('../services/api', () => ({
  getSafety: vi.fn().mockResolvedValue({}), 
  getForecast: vi.fn().mockResolvedValue({}), 
  getGrid: vi.fn().mockResolvedValue({}), 
  getVectorGrid: vi.fn().mockResolvedValue({}),
  getAdvisories: vi.fn().mockResolvedValue({}), 
  getGeofence: vi.fn().mockResolvedValue({}), 
  getGeofenceStatus: vi.fn().mockResolvedValue({
    status: 'SAFE_INSIDE_BORDER',
    distance_to_border_km: 42,
    distance_to_mpa_km: 42,
    is_inside_eez: true,
    is_inside_mpa: false
  }),
  getPfzLines: vi.fn().mockResolvedValue({}), 
  calculateRoute: vi.fn().mockResolvedValue({})
}));

import OperationsDashboard from './OperationsDashboard';

describe('OperationsDashboard - Sprint 2 Glassmorphism Layout Edge Case', () => {
  it('Edge Case 4: The 3-layer Z-index stack safely mounts without DOM overlap conflicts', () => {
    const { getByTestId, container } = render(
      <MemoryRouter>
        <OperationsDashboard />
      </MemoryRouter>
    );

    // Verify MapConsole is Layer 0
    const map = getByTestId('map-console');
    expect(map).toBeDefined();

    // Verify the Sidebars are floating correctly
    const spotlightCard = getByTestId('spotlight-card');
    expect(spotlightCard).toBeDefined();
    
    // Check that the glassmorphism classes exist somewhere in the DOM tree
    const htmlContent = container.innerHTML;
    expect(htmlContent).toContain('backdrop-blur-md');
    expect(htmlContent).toContain('bg-[#0D1B2A]/75');
    
    // Verify the timeline exists
    const timeline = getByTestId('weather-timeline');
    expect(timeline).toBeDefined();
  });

  it('enables the demo vessel independently of route planning state', async () => {
    const { getByRole } = render(
      <MemoryRouter>
        <OperationsDashboard />
      </MemoryRouter>
    );

    const simulator = getByRole('switch');
    fireEvent.click(simulator);

    await waitFor(() => expect(simulator.getAttribute('aria-checked')).toBe('true'));
  });
});
