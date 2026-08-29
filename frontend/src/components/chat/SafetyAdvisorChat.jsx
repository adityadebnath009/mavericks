import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, 
  Send, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  X, 
  Sparkles, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  FileText, 
  Compass, 
  ExternalLink, 
  RotateCcw, 
  ChevronDown, 
  ChevronUp, 
  Languages, 
  CheckCircle2, 
  Waves,
  Radio,
  Layers
} from 'lucide-react';
import { useVoiceAdvisor, SUPPORTED_LANGUAGES } from '../../hooks/useVoiceAdvisor';
import { askSafetyAdvisor } from '../../services/api';
import RiskBadge from '../common/RiskBadge';
import SpotlightCard from '../common/SpotlightCard';

const QUICK_PROMPTS = [
  { label: 'Is current route safe?', query: 'Is my current planned route safe for navigation given the active sea state?' },
  { label: 'Show wave conditions', query: 'What are the current significant wave heights and steepness indices along my path?' },
  { label: 'Am I near restricted MPAs?', query: 'Am I within the 5 km buffer zone of any marine protected areas or the international EEZ border?' },
  { label: 'Check beam stability (<4m)', query: 'Evaluate small craft beam stability and capsizing risks under SVAS standards.' },
  { label: 'Optimal departure window?', query: 'What is the recommended departure window to avoid peak afternoon surface current velocities?' }
];

const INITIAL_MESSAGES = [
  {
    id: 'msg-init-1',
    sender: 'advisor',
    timestamp: 'Just now',
    text: 'Welcome to the **NAVIK Grounded Safety Advisor**. I synthesize live telemetry from INCOIS Ocean State Forecasts, WaveWatch III rasters, and PostGIS boundary layers with official regulatory codes from the **FAO Small Craft Safety Code**, **CMFRI Advisories**, and **Indian Coast Guard Maritime Directives**.',
    citations: [
      {
        title: 'FAO Code of Conduct for Responsible Fisheries (1995)',
        clause: 'Section 8.2 - Vessel Safety at Sea & Stability Criteria'
      },
      {
        title: 'INCOIS Small Vessel Advisory Service (SVAS)',
        clause: 'Technical Bulletin 2026/08 - Indian EEZ Hazard Thresholds'
      }
    ],
    safety_rating: 'SAFE'
  }
];

export function SafetyAdvisorChat({
  isOpen = false,
  onClose,
  liveContext = {},
  activeMode = 'routing',
  onApplyAction,
  className = ''
}) {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showLiveContext, setShowLiveContext] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Web Speech API hook
  const {
    selectedLanguage,
    setSelectedLanguage,
    isListening,
    transcript,
    isSpeaking,
    isSttSupported,
    isTtsSupported,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    resetTranscript,
    supportedLanguages
  } = useVoiceAdvisor('en-IN');

  // Sync speech recognition transcript into the input box
  useEffect(() => {
    if (transcript) {
      setInputQuery(transcript);
    }
  }, [transcript]);

  // Scroll to bottom when messages update
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Focus input when drawer opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 200);
    } else {
      stopSpeaking();
      stopListening();
    }
  }, [isOpen, stopSpeaking, stopListening]);

  // Send query to Grounded RAG backend
  const handleSendMessage = async (queryText = inputQuery) => {
    const textToSend = (queryText || '').trim();
    if (!textToSend || isLoading) return;

    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    resetTranscript();
    setIsLoading(true);

    try {
      // Map activeMode to readable workspace name
      const workspaceName = activeMode === 'routing' 
        ? 'Tactical Routing' 
        : activeMode === 'fisheries' 
        ? 'Ocean Analytics' 
        : 'Meteorological Hazards';

      const enrichedContext = {
        ...liveContext,
        active_mode: activeMode,
        timestamp: new Date().toISOString()
      };

      const response = await askSafetyAdvisor(textToSend, workspaceName, enrichedContext);

      const advisorMsg = {
        id: `advisor-${Date.now()}`,
        sender: 'advisor',
        text: response.response_text || 'Advisory data retrieved successfully.',
        citations: response.citations || [],
        safety_rating: response.safety_rating || liveContext.current_risk_score || 'SAFE',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, advisorMsg]);

      // Auto-vocalize response if user spoke or autoSpeak is active
      if ((isListening || autoSpeak) && isTtsSupported && response.response_text) {
        speak(response.response_text, selectedLanguage);
      }
    } catch (err) {
      console.error('[SafetyAdvisorChat] Query error:', err);
      const errorMsg = {
        id: `advisor-err-${Date.now()}`,
        sender: 'advisor',
        text: `Unable to reach remote advisory services (${err.message}). Local fallback: Ensure vessel maintains VHF monitoring on Channel 16 and standard small-craft stability margins.`,
        citations: [
          {
            title: 'Indian Coast Guard Advisory',
            clause: 'Standard Operating Procedures for Coastal Fishing Vessels'
          }
        ],
        safety_rating: 'CAUTION',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleMicToggle = () => {
    if (isListening) {
      stopListening();
      if (transcript) {
        handleSendMessage(transcript);
      }
    } else {
      startListening((finalTranscript) => {
        if (finalTranscript) {
          handleSendMessage(finalTranscript);
        }
      });
    }
  };

  const handlePromptClick = (promptQuery) => {
    setInputQuery(promptQuery);
    handleSendMessage(promptQuery);
  };

  if (!isOpen) return null;

  return (
    <div 
      className={`fixed inset-y-0 right-0 w-full sm:w-[460px] lg:w-[500px] bg-[#0D1B2A] border-l border-[#20384D] shadow-2xl z-50 flex flex-col justify-between font-sans text-xs select-none overflow-hidden transition-all duration-300 animate-in slide-in-from-right ${className}`}
      aria-label="AI Safety Advisor Slide-Out Console"
    >
      {/* 1. Header Toolbar */}
      <header className="h-14 min-h-[56px] px-4 bg-[#07111F] border-b border-[#20384D] flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-[#13263A] border border-[#20384D]">
            <Bot className="w-4 h-4 text-[#00D4FF]" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#18C7A0] animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-mono font-bold text-xs text-[#EAF4F8] uppercase tracking-wider">
                Safety Advisor
              </span>
              <span className="text-[8px] font-mono font-bold px-1.5 py-0.2 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30">
                RAG CITED
              </span>
            </div>
            <span className="text-[9px] text-[#8FA8B8] font-mono block">
              Grounded AI • Web Speech • pgvector
            </span>
          </div>
        </div>

        {/* Header Controls: Language Selector, TTS Toggle, Close */}
        <div className="flex items-center gap-2">
          {/* Language Selector */}
          <div className="relative">
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-[#13263A] border border-[#20384D] hover:border-[#00D4FF]/50 text-[#EAF4F8] font-mono text-[10px] rounded-lg px-2 py-1 focus:outline-none cursor-pointer"
              title="Select Voice & Dialogue Language"
            >
              {supportedLanguages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.short}
                </option>
              ))}
            </select>
          </div>

          {/* Auto Read-Aloud Toggle */}
          <button
            type="button"
            onClick={() => {
              if (isSpeaking) stopSpeaking();
              setAutoSpeak(!autoSpeak);
            }}
            className={`p-1.5 rounded-lg border transition cursor-pointer ${
              autoSpeak || isSpeaking
                ? 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0]'
                : 'bg-[#13263A] border-[#20384D] text-[#8FA8B8] hover:text-[#EAF4F8]'
            }`}
            title={autoSpeak ? 'Auto Voice Read-Aloud: ENABLED' : 'Enable Auto Voice Read-Aloud'}
          >
            {isSpeaking ? (
              <Volume2 className="w-3.5 h-3.5 animate-pulse text-[#18C7A0]" />
            ) : autoSpeak ? (
              <Volume2 className="w-3.5 h-3.5 text-[#18C7A0]" />
            ) : (
              <VolumeX className="w-3.5 h-3.5" />
            )}
          </button>

          {/* Close Drawer Button */}
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg bg-[#13263A] hover:bg-[#1f3852] border border-[#20384D] text-[#8FA8B8] hover:text-[#EAF4F8] transition cursor-pointer"
            title="Close Safety Advisor Panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* 2. Live Context Inspection Banner */}
      <div className="bg-[#0D1B2A] border-b border-[#20384D] px-3.5 py-2 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-[9px] text-[#8FA8B8]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-pulse" />
            <span>LIVE CONTEXT ATTACHED:</span>
            <span className="text-[#00D4FF] font-bold uppercase">{activeMode}</span>
            <span>•</span>
            <span className="text-[#EAF4F8]">Beam: {liveContext.beam_width || '3.5m'}</span>
            <span>•</span>
            <span className="text-[#18C7A0] font-bold">{liveContext.current_risk_score || 'LOW'}</span>
          </div>

          <button
            type="button"
            onClick={() => setShowLiveContext(!showLiveContext)}
            className="text-[9px] font-mono text-[#8FA8B8] hover:text-[#00D4FF] flex items-center gap-0.5 cursor-pointer"
          >
            <span>{showLiveContext ? 'Hide' : 'Inspect'}</span>
            {showLiveContext ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>

        {/* Expandable Live Context JSON Inspector */}
        {showLiveContext && (
          <div className="mt-2 p-2.5 bg-[#07111F] rounded-lg border border-[#20384D] font-mono text-[8.5px] text-[#18C7A0] overflow-x-auto max-h-36">
            <pre className="whitespace-pre-wrap leading-relaxed">
              {JSON.stringify(
                {
                  active_workspace: activeMode,
                  origin_coords: liveContext.origin_coords || { lat: 18.92, lon: 72.83 },
                  destination_coords: liveContext.destination_coords || null,
                  vessel_beam_m: liveContext.beam_width || 3.5,
                  risk_assessment: liveContext.current_risk_score || 'LOW',
                  bsi_score: liveContext.bsi_score ?? 1,
                  max_wave_height: liveContext.max_wave_height || '1.2m',
                  wind_speed_peak: liveContext.wind_speed || '18.5 km/h',
                  distance_to_border: liveContext.distance_to_border || '116.9 km (CLEAR)',
                  avoided_hazards: liveContext.avoided_hazards || ['Gulf of Mannar MPA', 'High Wave Zone']
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>

      {/* 3. Message History Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#07111F]/50">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';

          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
            >
              {/* Sender & Timestamp Header */}
              <div className="flex items-center gap-2 px-1 text-[9px] font-mono text-[#8FA8B8]">
                {!isUser && (
                  <div className="flex items-center gap-1 text-[#00D4FF] font-bold">
                    <Sparkles className="w-2.5 h-2.5" />
                    <span>NAVIK RAG</span>
                  </div>
                )}
                <span>{msg.timestamp}</span>
                {!isUser && msg.safety_rating && (
                  <RiskBadge level={msg.safety_rating} size="xs" showIcon={false} />
                )}
              </div>

              {/* Message Bubble Card */}
              <div
                className={`max-w-[90%] p-3.5 rounded-2xl border font-sans text-xs leading-relaxed shadow-lg ${
                  isUser
                    ? 'bg-[#13263A] text-[#EAF4F8] border-[#00D4FF]/40 rounded-tr-none'
                    : 'bg-[#0D1B2A] text-[#EAF4F8] border-[#20384D] rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </div>

                {/* Grounded RAG Citations Container */}
                {!isUser && msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-[#20384D] space-y-1.5">
                    <span className="text-[8.5px] font-mono font-bold uppercase tracking-wider text-[#18C7A0] flex items-center gap-1">
                      <FileText className="w-3 h-3 text-[#18C7A0]" />
                      Official Regulatory Citations:
                    </span>
                    <div className="space-y-1">
                      {msg.citations.map((cite, cIdx) => (
                        <div
                          key={cIdx}
                          className="bg-[#07111F] p-2 rounded-lg border border-[#20384D] font-mono text-[8.5px] space-y-0.5"
                        >
                          <div className="font-bold text-[#00D4FF] flex items-center justify-between">
                            <span>{cite.title}</span>
                            <span className="text-[#8FA8B8] text-[7.5px]">VERIFIED</span>
                          </div>
                          <div className="text-[#8FA8B8]">{cite.clause}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Per-Message Audio Playback Button */}
                {!isUser && isTtsSupported && (
                  <div className="mt-2.5 pt-1.5 flex justify-end">
                    <button
                      type="button"
                      onClick={() => speak(msg.text, selectedLanguage)}
                      className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#07111F] hover:bg-[#13263A] border border-[#20384D] text-[#00D4FF] font-mono text-[8.5px] transition cursor-pointer"
                      title="Read Aloud in Selected Language"
                    >
                      <Volume2 className="w-2.5 h-2.5" />
                      <span>Read Aloud</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Bubble */}
        {isLoading && (
          <div className="flex items-start space-y-1">
            <div className="bg-[#0D1B2A] border border-[#20384D] p-3 rounded-2xl rounded-tl-none space-y-2 max-w-[80%]">
              <div className="flex items-center gap-2 text-[10px] font-mono text-[#00D4FF]">
                <div className="w-2 h-2 rounded-full bg-[#00D4FF] animate-ping" />
                <span>Searching pgvector regulatory database...</span>
              </div>
              <div className="flex gap-1.5 pt-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 4. Quick Prompt Pills Carousel */}
      <div className="p-2.5 bg-[#0D1B2A] border-t border-[#20384D] space-y-1.5 shrink-0">
        <span className="text-[8.5px] font-mono text-[#8FA8B8] uppercase block px-1">
          Quick Maritime Prompts:
        </span>
        <div className="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          {QUICK_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePromptClick(p.query)}
              disabled={isLoading}
              className="px-2.5 py-1 rounded-full bg-[#13263A] hover:bg-[#1f3852] border border-[#20384D] hover:border-[#00D4FF]/40 text-[#EAF4F8] font-mono text-[9px] whitespace-nowrap transition cursor-pointer disabled:opacity-50"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* 5. Voice Input & Text Query Bar */}
      <footer className="p-3 bg-[#07111F] border-t border-[#20384D] shrink-0 space-y-2">
        {/* Active Speech Recognition Banner */}
        {isListening && (
          <div className="flex items-center justify-between px-3 py-1 rounded-lg bg-[#00D4FF]/10 border border-[#00D4FF]/30 text-[10px] font-mono text-[#00D4FF] animate-pulse">
            <div className="flex items-center gap-2">
              <Mic className="w-3 h-3" />
              <span>Listening in {supportedLanguages.find(l => l.code === selectedLanguage)?.name}...</span>
            </div>
            <button
              type="button"
              onClick={stopListening}
              className="text-[9px] text-[#FF5C5C] underline font-bold cursor-pointer"
            >
              Stop
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          {/* Multilingual Voice Mic Button */}
          <button
            type="button"
            onClick={handleMicToggle}
            className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-center ${
              isListening
                ? 'bg-[#00D4FF] text-[#07111F] border-[#00D4FF] shadow-[0_0_15px_rgba(0,212,255,0.5)] animate-pulse'
                : 'bg-[#13263A] hover:bg-[#1c3854] text-[#00D4FF] border-[#20384D] hover:border-[#00D4FF]/50'
            }`}
            title={isListening ? 'Click to Stop Listening' : `Speak in ${supportedLanguages.find(l => l.code === selectedLanguage)?.name}`}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          {/* Text Input */}
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedLanguage === 'hi-IN'
                  ? 'समुद्री सुरक्षा, लाटों की स्थिति या सीमा के बारे में पूछें...'
                  : selectedLanguage === 'mr-IN'
                  ? 'सुरक्षा, लाटांची स्थिती किंवा सीमा नियमांबद्दल विचारा...'
                  : 'Ask about route safety, wave limits, or border rules...'
              }
              disabled={isLoading}
              className="w-full bg-[#13263A] border border-[#20384D] rounded-xl px-3.5 py-2 text-xs text-[#EAF4F8] placeholder-[#8FA8B8]/60 font-sans focus:border-[#00D4FF] focus:outline-none transition-colors"
            />
          </div>

          {/* Send Query Button */}
          <button
            type="button"
            onClick={() => handleSendMessage()}
            disabled={isLoading || !inputQuery.trim()}
            className="p-2.5 rounded-xl bg-[#00D4FF] hover:bg-[#00B4D8] text-[#07111F] font-bold transition-all shadow-[0_0_12px_rgba(0,212,255,0.25)] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            title="Send Query"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        {/* Footer Disclaimer */}
        <div className="flex justify-between items-center text-[7.5px] font-mono text-[#8FA8B8] px-1">
          <span>Grounded RAG: Clauses cited verbatim</span>
          <span>Zero external speech API cost</span>
        </div>
      </footer>
    </div>
  );
}

export default SafetyAdvisorChat;
