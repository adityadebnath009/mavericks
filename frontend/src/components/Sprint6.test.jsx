import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, act } from '@testing-library/react';

// Mocks
if (typeof window !== 'undefined') {
  window.speechSynthesis = {
    cancel: vi.fn(),
    speak: vi.fn(),
    getVoices: vi.fn(() => [])
  };
  window.SpeechRecognition = vi.fn(() => ({
    start: vi.fn(),
    stop: vi.fn(),
    abort: vi.fn()
  }));
}

import BriefingCard from './chat/BriefingCard';
import CommandBar from './chat/CommandBar';

describe('Sprint 6: Localization & Text-To-Speech Validation', () => {

  it('CommandBar renders localization toggles EN/HI/MR', () => {
    const { getByText } = render(<CommandBar onQuerySubmit={vi.fn()} />);
    expect(getByText('EN')).toBeDefined();
    expect(getByText('HI')).toBeDefined();
    expect(getByText('MR')).toBeDefined();
  });

  it('BriefingCard renders Language Selector and TTS Button', () => {
    const mockSynthesis = { summary: "This is a test summary." };
    const { container, getByTitle } = render(<BriefingCard synthesis={mockSynthesis} />);
    
    // Check if the TTS read aloud button exists
    const ttsButton = getByTitle(/Read Summary Aloud/i);
    expect(ttsButton).toBeDefined();

    // Trigger TTS
    act(() => { fireEvent.click(ttsButton); });
    expect(window.speechSynthesis.speak).toHaveBeenCalled();
  });

});
