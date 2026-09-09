import React from 'react';
import { Volume2, VolumeX, Languages } from 'lucide-react';
import { useVoiceAdvisor } from '../../hooks/useVoiceAdvisor';

const getBadgeStyle = (assessment) => {
  switch (assessment?.toUpperCase()) {
    case 'SAFE':
      return 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0] shadow-[0_0_15px_rgba(24,199,160,0.3)]';
    case 'UNSAFE':
      return 'bg-[#FF5C5C]/20 border-[#FF5C5C] text-[#FF5C5C] shadow-[0_0_15px_rgba(255,92,92,0.3)]';
    default:
      return 'bg-[#FFB547]/20 border-[#FFB547] text-[#FFB547] shadow-[0_0_15px_rgba(255,181,71,0.3)]';
  }
};

const BriefingCard = ({
  assessment = 'COMPUTED',
  certification = 'VALID',
  synthesis = null,
  ragFootnotes = [],
  followups = [],
  onFollowupClick
}) => {
  const {
    selectedLanguage,
    setSelectedLanguage,
    isSpeaking,
    isTtsSupported,
    speak,
    stopSpeaking,
    supportedLanguages
  } = useVoiceAdvisor('en-IN');

  const badgeStyle = getBadgeStyle(assessment);
  const isStructured = typeof synthesis === 'object' && synthesis !== null;
  const rawText = !isStructured ? synthesis : '';


  return (
    <div className="flex flex-col bg-[#07111F]/60 backdrop-blur-2xl border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.5)] transition-all duration-500">
      
      {/* Header Badge */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-gradient-to-r from-transparent to-white/[0.02]">
        <div className="flex items-center space-x-4">
          <div className={`px-4 py-1.5 border rounded-lg text-xs font-black font-mono tracking-widest uppercase ${badgeStyle}`}>
            {assessment}
          </div>
          <div className="flex items-center space-x-2 text-[#8FA8B8] text-xs font-mono">
            <span>CERTIFICATION:</span>
            <span className={certification === 'VALID' ? 'text-[#18C7A0] font-bold' : 'text-[#FFB547] font-bold'}>
              {certification}
            </span>
          </div>
        </div>
        
        {/* Sprint 6: Multilingual Web Speech API */}
        <div className="flex items-center space-x-3">
          {isTtsSupported && (
            <div className="flex items-center bg-[#07111F] rounded-lg border border-[#20384D] overflow-hidden">
              <div className="flex items-center px-2 py-1.5 border-r border-[#20384D]">
                <Languages className="w-3.5 h-3.5 text-[#8FA8B8] mr-1.5" />
                <select 
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="bg-transparent text-[#EAF4F8] text-[10px] font-mono outline-none cursor-pointer"
                >
                  {supportedLanguages.map(lang => (
                    <option key={lang.code} value={lang.code} className="bg-[#07111F]">
                      {lang.short} {lang.flag}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => isSpeaking ? stopSpeaking() : speak(isStructured ? synthesis.summary : rawText)}
                className={`px-3 py-1.5 flex items-center justify-center transition-colors cursor-pointer ${
                  isSpeaking 
                    ? 'bg-[#00D4FF]/20 text-[#00D4FF] hover:bg-[#00D4FF]/30' 
                    : 'bg-transparent text-[#8FA8B8] hover:text-[#00D4FF] hover:bg-white/5'
                }`}
                title={isSpeaking ? "Stop Reading" : "Read Summary Aloud"}
              >
                {isSpeaking ? <VolumeX className="w-4 h-4 animate-pulse" /> : <Volume2 className="w-4 h-4" />}
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Spacer to prevent header from duplicating since we closed the flex container above */}
      <div className="hidden">
      </div>

      {/* Structured Narrative Body */}
      <div className="p-6 text-[#EAF4F8] text-sm leading-relaxed font-sans space-y-6">
        {isStructured ? (
          <>
            {/* Executive Summary */}
            {synthesis.summary && (
              <div>
                <p className="text-base text-white font-medium">{synthesis.summary}</p>
              </div>
            )}
            
            {/* Hazards List */}
            {synthesis.hazards && synthesis.hazards.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#FFB547] mb-2 flex items-center">
                  <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                  Identified Hazards
                </h4>
                <ul className="space-y-1.5 pl-5">
                  {synthesis.hazards.map((hazard, i) => (
                    <li key={i} className="list-disc text-[#8FA8B8] marker:text-[#FFB547]">{hazard}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Operational Directives */}
            {synthesis.directives && synthesis.directives.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#00D4FF] mb-2 flex items-center">
                  <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  Operational Directives
                </h4>
                <ul className="space-y-1.5 pl-5">
                  {synthesis.directives.map((dir, i) => (
                    <li key={i} className="list-disc text-[#EAF4F8] marker:text-[#00D4FF]">{dir}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p>{rawText || 'Awaiting intelligence briefing...'}</p>
        )}
      </div>

      {/* RAG Footnotes / Citations */}
      {ragFootnotes && ragFootnotes.length > 0 && (
        <div className="px-6 pb-5">
          <div className="text-[10px] uppercase font-semibold tracking-wider text-[#8FA8B8] mb-2 border-b border-white/10 pb-1">
            Cited Sources
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {ragFootnotes.map((note, idx) => (
              <span key={idx} className="inline-flex items-center px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] text-[#00D4FF] hover:bg-white/10 cursor-pointer transition-colors">
                <span className="mr-1.5 opacity-70">📄</span>
                {note}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Action Tray (Dynamic Follow-ups) */}
      {followups && followups.length > 0 && (
        <div className="px-6 py-4 bg-white/[0.02] border-t border-white/10 flex flex-wrap gap-2">
          {followups.map((action, idx) => (
            <button
              key={idx}
              onClick={() => onFollowupClick && onFollowupClick(action)}
              className="px-4 py-2 bg-transparent hover:bg-[#00D4FF]/10 border border-[#00D4FF]/30 hover:border-[#00D4FF] rounded-lg text-xs font-medium text-[#EAF4F8] transition-all duration-300 flex items-center space-x-2"
            >
              <span className="text-[#00D4FF] animate-pulse">&gt;</span>
              <span>{action}</span>
            </button>
          ))}
        </div>
      )}
      
    </div>
  );
};

export default BriefingCard;
