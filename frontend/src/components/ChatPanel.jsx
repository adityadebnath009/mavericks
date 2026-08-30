// src/components/ChatPanel.jsx
import React, { useState, useEffect } from 'react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { SUPPORTED_LANGUAGES } from '../utils/languages';

export const ChatPanel = () => {
  const [selectedLang, setSelectedLang] = useState('en');
  const [messages, setMessages] = useState([]);
  
  const currentLocale = SUPPORTED_LANGUAGES[selectedLang].code;

  const { 
    isListening, 
    transcript, 
    error: sttError, 
    startListening, 
    stopListening 
  } = useSpeechRecognition(currentLocale);

  const { speak, isSpeaking, stop } = useSpeechSynthesis();

  // Handle the completion of a voice input
  useEffect(() => {
    if (!isListening && transcript) {
      handleUserSubmit(transcript);
    }
  }, [isListening, transcript]);

  const handleUserSubmit = async (text) => {
    if (!text.trim()) return;

    // 1. Add user message to UI
    setMessages(prev => [...prev, { role: 'user', text }]);

    // 2. Send to backend Intent Orchestrator (Mocked here)
    // In production, this calls POST /api/chat
    const agentResponse = `Received: "${text}". The weather is calm.`; 
    
    // 3. Add agent response to UI
    setMessages(prev => [...prev, { role: 'agent', text: agentResponse }]);

    // 4. Speak the response aloud in the selected language
    speak(agentResponse, currentLocale);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md border p-4">
      {/* Header & Language Selector */}
      <div className="flex justify-between items-center mb-4 pb-2 border-b">
        <h2 className="font-bold text-lg">ORCA Interaction Agent</h2>
        <select 
          value={selectedLang}
          onChange={(e) => setSelectedLang(e.target.value)}
          className="p-1 text-sm border rounded"
        >
          {Object.entries(SUPPORTED_LANGUAGES).map(([key, lang]) => (
            <option key={key} value={key}>
              {lang.label} ({lang.native})
            </option>
          ))}
        </select>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 rounded-lg max-w-[80%] ${
              msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {/* Live Transcript Preview */}
        {isListening && transcript && (
          <div className="flex justify-end">
             <div className="p-3 rounded-lg bg-blue-100 text-blue-800 italic opacity-70">
               {transcript}...
             </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {sttError && <p className="text-red-500 text-sm mb-2">{sttError}</p>}

      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`flex-1 py-3 px-4 rounded-lg font-bold text-white transition-colors ${
            isListening ? 'bg-red-500 hover:bg-red-600 animate-pulse' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isListening ? 'Stop Recording' : 'Hold to Speak'}
        </button>
        
        {isSpeaking && (
          <button 
            onClick={stop}
            className="px-4 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
          >
            Stop Audio
          </button>
        )}
      </div>
    </div>
  );
};