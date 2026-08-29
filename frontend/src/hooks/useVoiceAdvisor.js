import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Supported regional fishing languages for Indian coastal operations
 */
export const SUPPORTED_LANGUAGES = [
  { code: 'en-IN', name: 'English (Maritime)', short: 'EN', flag: '🇮🇳' },
  { code: 'hi-IN', name: 'हिन्दी (Hindi)', short: 'HI', flag: '🇮🇳' },
  { code: 'mr-IN', name: 'मराठी (Marathi)', short: 'MR', flag: '🇮🇳' }
];

/**
 * Custom React Hook: useVoiceAdvisor
 * Integrates browser-native Web Speech API (SpeechRecognition for STT and SpeechSynthesis for TTS).
 * Provides zero-cost multilingual voice input and read-aloud capabilities with graceful fallbacks.
 */
export function useVoiceAdvisor(initialLang = 'en-IN') {
  const [selectedLanguage, setSelectedLanguage] = useState(initialLang);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState(null);

  const recognitionRef = useRef(null);
  const onResultCallbackRef = useRef(null);

  // Check browser support
  const isSttSupported = typeof window !== 'undefined' && Boolean(
    window.SpeechRecognition || window.webkitSpeechRecognition
  );
  const isTtsSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const isSupported = isSttSupported || isTtsSupported;

  // Cleanup speech synthesis and recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (_) {}
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
        } catch (_) {}
      }
    };
  }, []);

  /**
   * Start Speech-to-Text (STT) Recognition
   */
  const startListening = useCallback((onResult) => {
    setError(null);
    setTranscript('');
    if (onResult) {
      onResultCallbackRef.current = onResult;
    }

    if (!isSttSupported) {
      console.warn('[useVoiceAdvisor] Web Speech Recognition not supported in this browser.');
      setError('Voice recognition is not supported in this browser. Please type your query.');
      return false;
    }

    // Stop any ongoing speech playback before listening
    if (isTtsSupported) {
      try {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      } catch (_) {}
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      recognition.lang = selectedLanguage;
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        let currentTranscript = '';
        for (let i = 0; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);

        // If finalized, notify parent
        const isFinal = event.results[event.results.length - 1].isFinal;
        if (isFinal && onResultCallbackRef.current) {
          onResultCallbackRef.current(currentTranscript);
        }
      };

      recognition.onerror = (event) => {
        console.warn('[useVoiceAdvisor] STT Error:', event.error);
        if (event.error !== 'no-speech') {
          setError(`Voice input error: ${event.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      return true;
    } catch (err) {
      console.error('[useVoiceAdvisor] Failed to start speech recognition:', err);
      setError(err.message);
      setIsListening(false);
      return false;
    }
  }, [isSttSupported, isTtsSupported, selectedLanguage]);

  /**
   * Stop Speech-to-Text (STT) Recognition
   */
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
    }
    setIsListening(false);
  }, []);

  /**
   * Read aloud text using Text-to-Speech (TTS)
   */
  const speak = useCallback((text, langCode = null) => {
    if (!text) return;
    setError(null);

    if (!isTtsSupported) {
      console.warn('[useVoiceAdvisor] Speech Synthesis not supported in this browser.');
      return;
    }

    try {
      // Cancel previous speech
      window.speechSynthesis.cancel();

      // Clean HTML / markdown formatting from text for clean vocal output
      const cleanText = text
        .replace(/<[^>]*>/g, '')
        .replace(/[*_#`~]/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .trim();

      const utterance = new SpeechSynthesisUtterance(cleanText);
      const targetLang = langCode || selectedLanguage;
      utterance.lang = targetLang;
      utterance.rate = 0.95; // Slightly measured rate for clear marine advisory delivery
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.warn('[useVoiceAdvisor] TTS Error:', event);
        setIsSpeaking(false);
      };

      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error('[useVoiceAdvisor] TTS synthesis exception:', err);
      setIsSpeaking(false);
    }
  }, [isTtsSupported, selectedLanguage]);

  /**
   * Stop any active audio playback
   */
  const stopSpeaking = useCallback(() => {
    if (isTtsSupported) {
      try {
        window.speechSynthesis.cancel();
      } catch (_) {}
    }
    setIsSpeaking(false);
  }, [isTtsSupported]);

  /**
   * Reset transcript buffer
   */
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return {
    selectedLanguage,
    setSelectedLanguage,
    isListening,
    transcript,
    isSpeaking,
    error,
    isSupported,
    isSttSupported,
    isTtsSupported,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    resetTranscript,
    supportedLanguages: SUPPORTED_LANGUAGES
  };
}

export default useVoiceAdvisor;
