import React, { useState } from 'react';

const getStatusColor = (assessment) => {
  switch (assessment?.toUpperCase()) {
    case 'SAFE':
      return 'text-[#18C7A0]'; // Sea Green
    case 'UNSAFE':
    case 'EXTREME':
      return 'text-[#FF5C5C]'; // Coral Red
    case 'HIGH':
    case 'MODERATE':
      return 'text-[#FFB547]'; // Amber
    default:
      return 'text-[#8FA8B8]'; // Blue Gray
  }
};

const EvidenceLedger = ({
  evidenceMet = 0,
  evidenceRequired = 0,
  assessment = 'UNKNOWN',
  certification = 'PENDING',
  isSafetyFloorTriggered = false,
  sources = [],
  ragFootnotes = [],
  className = ''
}) => {
  const [expandedFootnote, setExpandedFootnote] = useState(null);
  const percentage = evidenceRequired > 0 ? (Math.min(evidenceMet / evidenceRequired, 1)) * 100 : 0;
  const statusColor = getStatusColor(assessment);

  return (
    <div className={`flex flex-col bg-[#0D1B2A]/90 backdrop-blur-md border border-[#20384D] rounded-lg p-4 w-80 text-[#EAF4F8] shadow-2xl font-sans ${className}`}>
      <div className="flex items-center justify-between mb-4 border-b border-[#20384D] pb-2">
        <h2 className="text-[#8FA8B8] text-[11px] uppercase font-bold tracking-widest flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5 text-[#00D4FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
          Evidence Ledger
        </h2>
        {isSafetyFloorTriggered && (
          <div className="group relative">
            <svg className="w-3.5 h-3.5 text-[#FF5C5C]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
            <div className="absolute right-0 top-full mt-2 w-48 bg-[#07111F] text-[9px] text-[#FF5C5C] p-2 rounded border border-[#FF5C5C]/30 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              Deterministic Safety Floor Triggered: ML inference overridden.
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pr-1 space-y-5 custom-scrollbar">
        {/* 1. Completeness Meter */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <h3 className="text-[#8FA8B8] text-[9px] uppercase font-bold tracking-wider">Completeness</h3>
            <div className="text-[10px] font-mono text-[#00D4FF]">
              {evidenceMet} / {evidenceRequired}
            </div>
          </div>
          <div className="w-full bg-[#07111F] rounded-full h-1.5 border border-[#20384D] overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${percentage === 100 ? 'bg-[#18C7A0]' : 'bg-[#00D4FF]'}`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          {percentage < 100 && (
            <div className="text-[8px] text-[#FFB547] mt-1 text-right font-mono uppercase">Degraded Confidence</div>
          )}
        </div>

        {/* 2. Assessment & Certification */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <h3 className="text-[#8FA8B8] text-[9px] uppercase font-bold tracking-wider mb-1.5">Assessment</h3>
            <div className="flex items-center space-x-2 bg-[#07111F] px-2.5 py-1.5 rounded border border-[#20384D]">
              <div className={`w-1.5 h-1.5 rounded-full bg-current ${statusColor} ${assessment !== 'UNKNOWN' ? 'animate-pulse' : ''}`} />
              <span className={`font-mono text-[11px] font-bold ${statusColor}`}>{assessment}</span>
            </div>
          </div>
          <div>
            <h3 className="text-[#8FA8B8] text-[9px] uppercase font-bold tracking-wider mb-1.5">Certification</h3>
            <div className="flex items-center space-x-2 bg-[#07111F] px-2.5 py-1.5 rounded border border-[#20384D]">
              {certification === 'VALID' ? (
                <svg className="w-3 h-3 text-[#18C7A0]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              ) : (
                <svg className="w-3 h-3 text-[#FFB547]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              )}
              <span className={`font-mono text-[11px] font-bold ${certification === 'VALID' ? 'text-[#18C7A0]' : 'text-[#FFB547]'}`}>
                {certification}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Sources Tags */}
        <div>
          <h3 className="text-[#8FA8B8] text-[9px] uppercase font-bold tracking-wider mb-2">Sources Consulted</h3>
          <div className="flex flex-wrap gap-1.5">
            {(sources || []).map((source, idx) => {
              const isOffline = (source || '').toLowerCase().includes('offline') || (source || '').toLowerCase().includes('failed');
              const isCache = (source || '').toLowerCase().includes('cache');
              
              return (
                <div 
                  key={idx} 
                  className={`flex items-center space-x-1.5 px-2 py-1 rounded text-[9px] font-medium border ${
                    isOffline ? 'bg-[#FF5C5C]/10 border-[#FF5C5C]/30 text-[#FF5C5C]' :
                    isCache ? 'bg-[#FFB547]/10 border-[#FFB547]/30 text-[#FFB547]' :
                    'bg-[#07111F] border-[#20384D] text-[#EAF4F8] hover:border-[#00D4FF]'
                  } transition-colors`}
                >
                  <span className="opacity-70 text-[10px]">
                    {(source || '').includes('GEE') ? '🛰' : (source || '').includes('INCOIS') ? '🌊' : (source || '').includes('Meteo') ? '🌦' : '📄'}
                  </span>
                  <span className="truncate max-w-[150px]">{source}</span>
                </div>
              );
            })}
            {(!sources || sources.length === 0) && (
              <div className="text-[10px] text-[#8FA8B8] italic opacity-50 font-mono">No external sources connected.</div>
            )}
          </div>
        </div>

        {/* 4. RAG Footnotes */}
        <div>
          <h3 className="text-[#8FA8B8] text-[9px] uppercase font-bold tracking-wider mb-2">Compliance Footnotes</h3>
          <div className="space-y-1.5">
            {(ragFootnotes || []).map((footnote, idx) => (
              <div 
                key={idx}
                onClick={() => setExpandedFootnote(expandedFootnote === idx ? null : idx)}
                className="group cursor-pointer bg-[#07111F] rounded border border-[#20384D] hover:border-[#00D4FF]/50 transition-colors"
              >
                <div className="flex items-start p-2 gap-2">
                  <div className="text-[#00D4FF] font-mono text-[9px] mt-0.5">[{idx + 1}]</div>
                  <div className={`text-[10px] text-[#8FA8B8] group-hover:text-[#EAF4F8] transition-colors leading-relaxed ${expandedFootnote === idx ? '' : 'line-clamp-2'}`}>
                    {footnote}
                  </div>
                </div>
              </div>
            ))}
            {(!ragFootnotes || ragFootnotes.length === 0) && (
              <div className="text-[10px] text-[#8FA8B8] italic opacity-50 font-mono p-2 bg-[#07111F] rounded border border-[#20384D] border-dashed">
                No official compliance documents cited for this assessment.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvidenceLedger;
