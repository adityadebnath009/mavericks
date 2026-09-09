import React from 'react';
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import EvidenceLedger from './EvidenceLedger';

describe('EvidenceLedger Component', () => {
  it('1. Renders default empty state safely', () => {
    expect(() => render(<EvidenceLedger />)).not.toThrow();
  });

  it('2. Calculates 100% completeness correctly', () => {
    const { getByText } = render(<EvidenceLedger evidenceMet={4} evidenceRequired={4} />);
    expect(getByText('4 / 4')).toBeDefined();
  });

  it('3. Shows degraded confidence when evidence is missing', () => {
    const { getByText } = render(<EvidenceLedger evidenceMet={2} evidenceRequired={4} />);
    expect(getByText('Degraded Confidence')).toBeDefined();
  });

  it('4. Renders safety floor lock icon when triggered', () => {
    const { container } = render(<EvidenceLedger isSafetyFloorTriggered={true} />);
    // Look for the specific SVG lock icon stroke color or hover div
    expect(container.innerHTML).toContain('Deterministic Safety Floor Triggered');
  });

  it('5. Renders RAG footnotes successfully', () => {
    const { getByText } = render(<EvidenceLedger ragFootnotes={['Coast Guard Act Section 4', 'FAO Guideline']} />);
    expect(getByText('Coast Guard Act Section 4')).toBeDefined();
    expect(getByText('FAO Guideline')).toBeDefined();
  });

  it('6. Safely handles null arrays for sources and footnotes', () => {
    expect(() => render(<EvidenceLedger sources={null} ragFootnotes={null} />)).not.toThrow();
  });
  
  it('7. Renders offline/cached badges gracefully', () => {
    const { getByText } = render(<EvidenceLedger sources={['GEE (Offline)', 'INCOIS Cache']} />);
    expect(getByText('GEE (Offline)')).toBeDefined();
    expect(getByText('INCOIS Cache')).toBeDefined();
  });
});
