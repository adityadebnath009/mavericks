// src/hooks/useSpeechRecognition.ts
import { useState, useEffect, useCallback, useRef } from 'react';

// Handle vendor prefixes
const SpeechRecognition = 
  window.SpeechRecognition || window.webkitSpeechRecognition;

export function useSpeechRecognition(languageCode = 'en-IN') {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!SpeechRecognition) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = languageCode;

    recognition.onresult = (event) => {
      let currentTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        currentTranscript += event.results[i][0].transcript;
      }
      setTranscript(currentTranscript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      setError(event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, [languageCode]);

  const startListening = useCallback(() => {
    setError(null);
    setTranscript('');
    try {
      recognitionRef.current?.start();
      setIsListening(true);
    } catch (err) {
      console.error('Failed to start recognition', err);
    }
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  return { isListening, transcript, error, startListening, stopListening };
}