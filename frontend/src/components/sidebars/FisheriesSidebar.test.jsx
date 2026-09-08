import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { FisheriesSidebar } from './FisheriesSidebar';

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  Fish: () => <div data-testid="icon-fish" />,
  Layers: () => <div data-testid="icon-layers" />,
  Eye: () => <div data-testid="icon-eye" />,
  EyeOff: () => <div data-testid="icon-eyeoff" />,
  MapPin: () => <div data-testid="icon-mappin" />,
  Navigation: () => <div data-testid="icon-navigation" />,
  Sparkles: () => <div data-testid="icon-sparkles" />,
  Thermometer: () => <div data-testid="icon-thermometer" />,
  Droplet: () => <div data-testid="icon-droplet" />,
  Compass: () => <div data-testid="icon-compass" />,
  Waves: () => <div data-testid="icon-waves" />,
  Wind: () => <div data-testid="icon-wind" />,
  Activity: () => <div data-testid="icon-activity" />,
  ChevronRight: () => <div data-testid="icon-chevronright" />,
  ShieldCheck: () => <div data-testid="icon-shieldcheck" />,
  Zap: () => <div data-testid="icon-zap" />,
  Info: () => <div data-testid="icon-info" />
}));

test('renders dynamic offshore name and High Catch Opportunity Score', () => {
  const mockPfz = [
    {
      id: 101,
      properties: {
        offshore_name: 'Kozhikode',
        high_catch_score: 92,
        sst_median: 27.5,
        chl_median: 0.85
      }
    }
  ];

  render(
    <FisheriesSidebar 
      pfzList={mockPfz} 
      hoveredPfzId={null}
      onHoverPfz={() => {}}
      onSelectPfz={() => {}}
    />
  );

  // Verify the dynamic offshore name is rendered
  const cardTitle = screen.getByText('PFZ - Offshore Kozhikode');
  expect(cardTitle).toBeDefined();

  // Verify the score is rendered
  const scoreText = screen.getByText('Score: 92/100');
  expect(scoreText).toBeDefined();
  
  // Verify SST/CHL
  expect(screen.getByText('27.5°C')).toBeDefined();
  expect(screen.getByText('0.85 mg/m³')).toBeDefined();
});
