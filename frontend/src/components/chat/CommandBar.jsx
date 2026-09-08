import React, { useState, useEffect, useRef } from 'react';

const CommandBar = ({ onQuerySubmit }) => {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState('en-IN');
  const recognitionRef = useRef(null);

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event) => {
        const currentTranscript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        setQuery(currentTranscript);
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // Update recognition language when language state changes
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = language;
    }
  }, [language]);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
    } else {
      setQuery(''); // Clear existing query for fresh dictation
      recognitionRef.current?.start();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onQuerySubmit) {
      onQuerySubmit(query.trim(), language);
      setQuery('');
    }
  };

  return (
    <div className="w-full bg-[#0D1B2A]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-4 flex flex-col items-center shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
      
      {/* Localization Toggles */}
      <div className="flex space-x-4 mb-3 w-full max-w-4xl px-2">
        <span className="text-[#8FA8B8] text-[10px] uppercase font-bold tracking-widest mt-1">
          Input Lang:
        </span>
        <div className="flex space-x-2">
          {[{ code: 'en-IN', label: 'EN' }, { code: 'hi-IN', label: 'HI' }, { code: 'mr-IN', label: 'MR' }].map(lang => (
            <button
              key={lang.code}
              type="button"
              onClick={() => setLanguage(lang.code)}
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
          className="w-full bg-[#13263A] border border-[#20384D] rounded-lg py-3 pl-10 pr-16 text-[#EAF4F8] font-mono focus:outline-none focus:border-[#00D4FF] focus:ring-1 focus:ring-[#00D4FF] placeholder-[#8FA8B8]/50 transition-all shadow-inner"
        />

        {/* Voice Dictation Button */}
        <button
          type="button"
          onClick={toggleRecording}
          disabled={!recognitionRef.current}
          className={`absolute right-3 p-2 rounded-full transition-all flex items-center justify-center ${
            isRecording 
              ? 'bg-[#18C7A0]/20 text-[#18C7A0] animate-pulse shadow-[0_0_10px_rgba(24,199,160,0.5)]' 
              : 'text-[#8FA8B8] hover:text-[#00D4FF] hover:bg-[#20384D]/50'
          }`}
          title={!recognitionRef.current ? "Web Speech API not supported in this browser" : "Voice Dictation"}
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
    </div>
  );
};

export default CommandBar;
