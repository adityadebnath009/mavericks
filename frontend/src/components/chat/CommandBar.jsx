import React, { useState, useEffect, useRef } from 'react';

const toWavBase64 = (chunks, sampleRate = 8000) => {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const buffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(buffer);
  const write = (offset, value) => view.setUint32(offset, value, true);
  view.setUint32(0, 0x52494646, false); write(4, 36 + length * 2);
  view.setUint32(8, 0x57415645, false); view.setUint32(12, 0x666d7420, false);
  write(16, 16); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  write(24, sampleRate); write(28, sampleRate * 2); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  view.setUint32(36, 0x64617461, false); write(40, length * 2);
  let offset = 44;
  chunks.forEach((chunk) => chunk.forEach((sample) => {
    view.setInt16(offset, Math.max(-1, Math.min(1, sample)) * 0x7fff, true);
    offset += 2;
  }));
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return btoa(binary);
};

const CommandBar = ({ onQuerySubmit, language: controlledLanguage, onLanguageChange }) => {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isSttSupported, setIsSttSupported] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [voiceStatus, setVoiceStatus] = useState('');
  const [localLanguage, setLocalLanguage] = useState('en-IN');
  const language = controlledLanguage || localLanguage;
  const changeLanguage = (nextLanguage) => onLanguageChange ? onLanguageChange(nextLanguage) : setLocalLanguage(nextLanguage);
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const audioChunksRef = useRef([]);
  const isIntentionallyRecording = useRef(false);
  const finalTranscriptRef = useRef('');
  const languageRef = useRef(language);

  useEffect(() => { languageRef.current = language; }, [language]);

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    // Bhashini ASR is the primary path. Web Speech stays available only as a
    // browser fallback for environments which cannot supply microphone PCM.
    setIsSttSupported(Boolean(navigator.mediaDevices?.getUserMedia || SpeechRecognition));
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true; // KEEP ALIVE! Don't shut off instantly
      recognition.interimResults = true;

      recognition.onstart = () => {
        setIsRecording(true);
        setVoiceStatus('Listening…');
      };

      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
          else interimTranscript += event.results[i][0].transcript;
        }
        if (finalTranscript) finalTranscriptRef.current += finalTranscript;
        setQuery(`${finalTranscriptRef.current}${interimTranscript}`);
      };

      recognition.onerror = (event) => {
        const message = event.error === 'not-allowed' || event.error === 'service-not-allowed'
          ? 'Microphone access was denied. Allow it in your browser settings, or type your query.'
          : `Voice input failed (${event.error}). You can type your query instead.`;
        setVoiceError(message);
        if (event.error === 'no-speech') {
          setVoiceStatus('No speech detected. Continuing to listen…');
        } else {
          isIntentionallyRecording.current = false;
          setIsRecording(false);
        }
      };

      recognition.onend = () => {
        // Chrome aggressively kills the mic on silence. Auto-restart if we didn't manually stop it.
        if (isIntentionallyRecording.current) {
          try {
            recognition.lang = languageRef.current;
            recognition.start();
          } catch(e) {
            setIsRecording(false);
            isIntentionallyRecording.current = false;
          }
        } else {
          setIsRecording(false);
        }
      };

      recognitionRef.current = recognition;
    }
    return () => {
      isIntentionallyRecording.current = false;
      if (typeof recognitionRef.current?.abort === 'function') recognitionRef.current.abort();
      processorRef.current?.disconnect?.();
      streamRef.current?.getTracks?.().forEach((track) => track.stop());
      audioContextRef.current?.close?.();
      recognitionRef.current = null;
    };
  }, []);

  // Update recognition language when language state changes
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = language;
    }
  }, [language]);

  const startBhashiniRecording = async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.AudioContext) return false;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      const context = new window.AudioContext({ sampleRate: 8000 });
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);
      audioChunksRef.current = [];
      processor.onaudioprocess = (event) => audioChunksRef.current.push(new Float32Array(event.inputBuffer.getChannelData(0)));
      source.connect(processor);
      processor.connect(context.destination);
      streamRef.current = stream;
      audioContextRef.current = context;
      processorRef.current = processor;
      setIsRecording(true);
      setVoiceStatus('Listening securely with Bhashini… Tap the microphone again when finished.');
      return true;
    } catch (error) {
      const denied = error?.name === 'NotAllowedError' || error?.name === 'SecurityError';
      setVoiceError(denied
        ? 'Microphone access was denied. Allow it in browser settings, then try again or type your query.'
        : 'Microphone could not start. You can type your query instead.');
      return false;
    }
  };

  const stopBhashiniRecording = async () => {
    const chunks = audioChunksRef.current;
    processorRef.current?.disconnect?.();
    streamRef.current?.getTracks?.().forEach((track) => track.stop());
    await audioContextRef.current?.close?.();
    processorRef.current = null; streamRef.current = null; audioContextRef.current = null;
    setIsRecording(false);
    if (!chunks.length) {
      setVoiceError('No speech was captured. Please try again or type your query.');
      return;
    }
    setVoiceStatus('Transcribing securely with Bhashini…');
    try {
      const response = await fetch('/api/chat/transcribe', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_base64: toWavBase64(chunks), language }),
      });
      const result = await response.json();
      if (!response.ok || !result.text) throw new Error(result.detail || 'No transcript returned');
      setQuery((current) => `${current}${current.trim() ? ' ' : ''}${result.text}`);
      setVoiceStatus('Speech transcribed. Review or submit your query.');
    } catch (error) {
      setVoiceError(`Bhashini speech-to-text is unavailable (${error.message}). You can type your query instead.`);
    }
  };

  const toggleRecording = async () => {
    if (!isSttSupported) {
      setVoiceError('Voice recognition is not available in this browser. Please type your query.');
      return;
    }
    if (isRecording) {
      if (streamRef.current) {
        await stopBhashiniRecording();
        return;
      }
      isIntentionallyRecording.current = false;
      recognitionRef.current?.stop();
      setIsRecording(false);
      setVoiceStatus('Voice input stopped.');
    } else {
      setVoiceError('');
      setVoiceStatus('Starting voice input…');
      finalTranscriptRef.current = query ? `${query.trim()} ` : '';
      if (await startBhashiniRecording()) return;
      if (!recognitionRef.current) return;
      isIntentionallyRecording.current = true;
      try {
        recognitionRef.current.lang = language;
        recognitionRef.current?.start();
        setIsRecording(true);
      } catch (e) {
          setVoiceError('Voice input could not start. Please try again or type your query.');
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onQuerySubmit) {
      // A submitted transcript is final. Stop Chrome's silence-restart loop
      // before the network request begins; the next microphone click creates
      // a deliberate new listening session.
      isIntentionallyRecording.current = false;
      if (streamRef.current) {
        // A recording can be completed before form submission only when the
        // user presses the microphone again, so do not submit incomplete PCM.
        setVoiceError('Stop voice input before submitting so Bhashini can transcribe it.');
        return;
      }
      recognitionRef.current?.stop?.();
      setIsRecording(false);
      setVoiceStatus('Voice input submitted.');
      onQuerySubmit(query.trim(), language);
      setQuery('');
    }
  };

  return (
    <div className="w-full bg-[#0D1B2A]/80 backdrop-blur-xl border border-[#00D4FF]/30 hover:border-[#00D4FF]/60 rounded-3xl p-4 flex flex-col items-center shadow-[0_0_30px_rgba(0,212,255,0.1)] transition-all duration-300">
      
      {/* Localization Toggles */}
      <div className="flex items-center space-x-4 mb-3 w-full max-w-4xl px-4">
        <span className="text-[#8FA8B8] text-[10px] uppercase font-bold tracking-widest mt-1">
          Input Lang:
        </span>
        <div className="flex space-x-2">
          {[{ code: 'en-IN', label: 'EN' }, { code: 'hi-IN', label: 'HI' }, { code: 'mr-IN', label: 'MR' }].map(lang => (
            <button
              key={lang.code}
              type="button"
              onClick={() => changeLanguage(lang.code)}
              className={`text-xs px-2 py-0.5 rounded border transition-colors ${
                language === lang.code
                  ? 'border-[#00D4FF] bg-[#13263A] text-[#00D4FF]'
                  : 'border-[#20384D] text-[#8FA8B8] hover:border-[#8FA8B8]'
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Terminal Input Bar */}
      <form onSubmit={handleSubmit} className="flex items-center w-full max-w-4xl relative">
        <div className="absolute left-4 text-[#00D4FF] font-mono text-lg font-bold">
          &gt;
        </div>
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter operational query or activate voice command..."
          className="w-full bg-[#07111F]/50 border border-[#20384D] rounded-full py-4 pl-12 pr-16 text-[#EAF4F8] font-mono text-sm focus:outline-none focus:border-[#00D4FF] focus:ring-1 focus:ring-[#00D4FF] placeholder-[#8FA8B8]/40 transition-all shadow-inner"
        />

        {/* Voice Dictation Button */}
        <button
          type="button"
          onClick={toggleRecording}
          disabled={!isSttSupported}
          className={`absolute right-3 p-2 rounded-full transition-all flex items-center justify-center ${
            isRecording 
              ? 'bg-[#18C7A0]/20 text-[#18C7A0] animate-pulse shadow-[0_0_10px_rgba(24,199,160,0.5)]' 
              : 'text-[#8FA8B8] hover:text-[#00D4FF] hover:bg-[#20384D]/50'
          }`}
          aria-label="Start or stop voice dictation"
          title={!isSttSupported ? "Web Speech API not supported in this browser" : "Voice Dictation"}
        >
          {isRecording ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <rect x="9" y="9" width="6" height="6" fill="currentColor"></rect>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 1v22M4.22 4.22l15.56 15.56M1 12h22M4.22 19.78l15.56-15.56" opacity="0.3"></path>
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
            </svg>
          )}
        </button>
      </form>
      {(voiceError || voiceStatus) && <p role="status" aria-live="polite" className={`mt-2 w-full px-4 text-xs ${voiceError ? 'text-[#FFB547]' : 'text-[#8FA8B8]'}`}>{voiceError || voiceStatus}</p>}
    </div>
  );
};

export default CommandBar;
