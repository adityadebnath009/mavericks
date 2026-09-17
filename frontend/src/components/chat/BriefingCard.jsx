import React from 'react';
import { Volume2, VolumeX, Languages } from 'lucide-react';
import { useVoiceAdvisor } from '../../hooks/useVoiceAdvisor';

const getBadgeStyle = (assessment) => {
  switch (assessment?.toUpperCase()) {
    case 'SAFE':
      return 'bg-[#18C7A0]/20 border-[#18C7A0] text-[#18C7A0] shadow-[0_0_15px_rgba(24,199,160,0.3)]';
    case 'UNSAFE':
    case 'EXTREME':
      return 'bg-[#FF5C5C]/20 border-[#FF5C5C] text-[#FF5C5C] shadow-[0_0_15px_rgba(255,92,92,0.3)]';
    default:
      return 'bg-[#FFB547]/20 border-[#FFB547] text-[#FFB547] shadow-[0_0_15px_rgba(255,181,71,0.3)]';
  }
};

const citationLabel = (citation) => typeof citation === 'string' ? citation : citation?.title || 'Scholarly source';
const citationHref = (citation) => citation && typeof citation === 'object' ? (citation.landingPageUrl || citation.doi || citation.id) : null;

const BriefingCard = ({
  assessment = 'COMPUTED',
  certification = 'VALID',
  synthesis = null,
  safetyEvidence = null,
  explainability = null,
  sourceStatuses = [],
  ragFootnotes = [],
  followups = [],
  onFollowupClick,
  canRouteToPfz = false,
  onRouteToPfz,
  narrativeAi = null,
  language: controlledLanguage,
  onLanguageChange
}) => {
  const {
    selectedLanguage,
    setSelectedLanguage,
    isSpeaking,
    isTtsSupported,
    voiceUnavailable,
    error: voiceError,
    speak,
    stopSpeaking,
    supportedLanguages
  } = useVoiceAdvisor('en-IN');
  const language = controlledLanguage || selectedLanguage;
  const changeLanguage = (nextLanguage) => onLanguageChange ? onLanguageChange(nextLanguage) : setSelectedLanguage(nextLanguage);

  const badgeStyle = getBadgeStyle(assessment);
  const isStructured = typeof synthesis === 'object' && synthesis !== null;
  const rawText = !isStructured ? synthesis : '';


  return (
    <div className={`flex flex-col bg-[#07111F]/88 backdrop-blur-sm border rounded-xl w-full max-w-2xl overflow-hidden shadow-xl transition-all duration-500 ${
      assessment?.toUpperCase() === 'SAFE' ? 'border-[#18C7A0]/45' :
      ['UNSAFE', 'EXTREME'].includes(assessment?.toUpperCase()) ? 'border-[#FF5C5C]/45' :
      'border-[#FFB547]/45'
    }`}>
      
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
                  value={language}
                  onChange={(e) => changeLanguage(e.target.value)}
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
                onClick={() => isSpeaking ? stopSpeaking() : speak(isStructured ? (synthesis.executive_summary || synthesis.summary || '') : rawText, language)}
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
      <div className="p-4 sm:p-5 text-[#EAF4F8] text-sm leading-relaxed font-sans space-y-4">
        {!isTtsSupported && <p role="status" className="rounded-md border border-[#FFB547]/35 bg-[#FFB547]/10 px-2 py-1 text-xs text-[#FFB547]">Text-to-speech is unavailable in this browser; the answer remains available as text.</p>}
        {voiceUnavailable && <p role="status" className="rounded-md border border-[#FFB547]/35 bg-[#FFB547]/10 px-2 py-1 text-xs text-[#FFB547]">{voiceError || 'Voice unavailable for selected language; the answer remains available as text.'}</p>}
        {narrativeAi?.state === 'LIVE' && <p role="status" className="rounded-md border border-[#18C7A0]/35 bg-[#18C7A0]/10 px-2 py-1 text-xs text-[#18C7A0]">Grounded OpenAI narrative · {narrativeAi.model || 'configured model'}{narrativeAi.latencyMs != null ? ` · ${Math.round(narrativeAi.latencyMs)} ms` : ''}</p>}
        {narrativeAi?.state === 'UNAVAILABLE' && <p role="status" className="rounded-md border border-[#FFB547]/35 bg-[#FFB547]/10 px-2 py-1 text-xs text-[#FFB547]">Narrative AI unavailable — validated evidence guidance is shown. {narrativeAi.reason || ''}</p>}
        {isStructured ? (
          <>
            {/* Executive Summary */}
            {(synthesis.executive_summary || synthesis.summary) && (
              <div>
                <p className="text-base text-[#17303A] font-medium">{synthesis.executive_summary || synthesis.summary}</p>
              </div>
            )}
            {synthesis.plain_language_meaning && <p className="rounded-md border border-[#20384D]/70 bg-[#07111F]/55 px-3 py-2 text-xs text-[#8FA8B8]"><span className="font-semibold text-[#EAF4F8]">What this means:</span> {synthesis.plain_language_meaning}</p>}
            {synthesis.fisherman_advisory && <section className="rounded-lg border border-[#18C7A0]/40 bg-[#18C7A0]/[0.07] p-3" aria-label="What you should do now">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#18C7A0]">What you should do now</h4>
              <p className="mt-2 text-base font-semibold text-[#EAF4F8]">{synthesis.fisherman_advisory.headline}</p>
              {synthesis.fisherman_advisory.reasons?.length > 0 && <div className="mt-3 space-y-2">{synthesis.fisherman_advisory.reasons.map((reason, index) => <div key={`${reason.title}-${index}`} className="border-l-2 border-[#FFB547] pl-2 text-xs"><p className="font-semibold text-[#EAF4F8]">{reason.title}</p><p className="text-[#8FA8B8]">{reason.text}</p></div>)}</div>}
              {synthesis.fisherman_advisory.actions?.length > 0 && <div className="mt-3 border-t border-[#18C7A0]/20 pt-2"><p className="text-[10px] font-bold uppercase tracking-widest text-[#00D4FF]">Before you leave</p><ul className="mt-1.5 space-y-1 pl-4 text-xs text-[#EAF4F8]">{synthesis.fisherman_advisory.actions.map((action, index) => <li key={`${action}-${index}`} className="list-disc marker:text-[#00D4FF]">{action}</li>)}</ul></div>}
            </section>}
            {synthesis.limitations?.length > 0 && <section className="rounded-md border border-[#FFB547]/25 bg-[#FFB547]/5 px-3 py-2"><h4 className="text-[10px] font-bold uppercase tracking-widest text-[#FFB547]">What this check cannot confirm</h4><ul className="mt-1 space-y-1 pl-4 text-xs text-[#8FA8B8]">{synthesis.limitations.map((item, index) => <li key={`${item}-${index}`} className="list-disc">{item}</li>)}</ul></section>}
            
            {/* Hazards List */}
            {!synthesis.fisherman_advisory && (synthesis.identified_hazards || synthesis.hazards)?.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#FFB547] mb-2 flex items-center">
                  <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                  Identified Hazards
                </h4>
                <ul className="space-y-1.5 pl-5">
                  {(synthesis.identified_hazards || synthesis.hazards).map((hazard, i) => (
                    <li key={i} className="list-disc text-[#8FA8B8] marker:text-[#FFB547]">{hazard.text || hazard}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Operational Directives */}
            {!synthesis.fisherman_advisory && (synthesis.operational_directives || synthesis.directives)?.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase font-bold tracking-widest text-[#00D4FF] mb-2 flex items-center">
                  <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  Operational Directives
                </h4>
                <ul className="space-y-1.5 pl-5">
                  {(synthesis.operational_directives || synthesis.directives).map((dir, i) => (
                    <li key={i} className="list-disc text-[#EAF4F8] marker:text-[#00D4FF]">{dir.text || dir}</li>
                  ))}
                </ul>
              </div>
            )}
            {safetyEvidence && <details className="rounded-lg border border-[#20384D]/70 bg-[#07111F]/65 p-3" aria-label="Technical safety evidence"><summary className="cursor-pointer text-[10px] font-bold uppercase tracking-widest text-[#00D4FF]">Technical details for crew and judges</summary><section className="mt-3">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#00D4FF]">ORCA safety evidence</h4>
              <div className="mt-2 grid gap-2 text-xs text-[#8FA8B8] sm:grid-cols-2">
                <div><span className="font-medium text-[#EAF4F8]">Deterministic ORCA BSI:</span> {safetyEvidence.bsiEvidence?.state === 'LIVE' ? `${Number(safetyEvidence.bsi?.severityScore).toFixed(0)}/100 (${safetyEvidence.bsi?.report?.confidence || 'unknown'} confidence)` : 'score withheld — required environmental evidence is incomplete.'}</div>
                <div><span className="font-medium text-[#EAF4F8]">ML risk model:</span> {safetyEvidence.mlEvidence?.state === 'LIVE' ? `${safetyEvidence.mlRisk?.ml_risk_class || 'unknown'} (${safetyEvidence.mlRisk?.model_version || 'active model'})` : 'unavailable; deterministic fallback is not reported as ML.'}</div>
              </div>
              <div className="mt-3 border-t border-[#20384D]/70 pt-3" aria-label="Why this decision">
                <h5 className="text-[10px] font-bold uppercase tracking-widest text-[#18C7A0]">Why this decision</h5>
                <div className="mt-2 grid gap-2 text-xs text-[#8FA8B8] sm:grid-cols-2">
                  <p><span className="font-medium text-[#EAF4F8]">Weather:</span> {safetyEvidence.weather?.state === 'UNAVAILABLE' ? 'unavailable' : [`wind ${safetyEvidence.weather?.windSpeedKmh ?? '—'} km/h`, `gusts ${safetyEvidence.weather?.windGustKmh ?? '—'} km/h`, `visibility ${safetyEvidence.weather?.visibilityM ?? '—'} m`].join(' · ')}</p>
                  <p><span className="font-medium text-[#EAF4F8]">Sea state:</span> {safetyEvidence.marine?.state === 'UNAVAILABLE' ? 'unavailable' : [`waves ${safetyEvidence.marine?.waveHeightM ?? '—'} m`, `swell ${safetyEvidence.marine?.swellHeightM ?? '—'} m`, `current ${safetyEvidence.marine?.currentSpeedMs ?? '—'} m/s`].join(' · ')}</p>
                  <p><span className="font-medium text-[#EAF4F8]">Geofence:</span> returned in the map and evidence ledger for the selected point.</p>
                  <p className="text-[#FFB547]"><span className="font-medium text-[#EAF4F8]">Official IMD:</span> {safetyEvidence.officialWarning?.state || 'UNAVAILABLE'} — {safetyEvidence.officialWarning?.reason || 'official warning verification is not available.'}</p>
                </div>
                {safetyEvidence.hazards?.length > 0 && <p className="mt-2 rounded border border-[#FFB547]/25 bg-[#FFB547]/5 px-2 py-1.5 text-xs text-[#FFB547]">Computed hazard alert: {safetyEvidence.hazards.join(' · ')}</p>}
              </div>
            </section>
            {explainability?.drivers?.length > 0 && <section className="mt-3 rounded-lg border border-[#00D4FF]/35 bg-[#07111F]/65 p-3" aria-label="Explainable decision trace">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#00D4FF]">Explainable decision trace</h4>
              <p className="mt-1 text-xs text-[#8FA8B8]">Each item states the observed evidence, what it means, and its effect on this verdict.</p>
              <div className="mt-3 space-y-2">
                {explainability.drivers.map((driver, index) => <div key={`${driver.label}-${index}`} className={`rounded border px-2.5 py-2 text-xs ${driver.kind === 'HAZARD' || driver.kind === 'LIMIT' ? 'border-[#FFB547]/30 bg-[#FFB547]/5' : 'border-[#20384D] bg-[#13263A]/45'}`}>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3"><span className="font-semibold text-[#EAF4F8]">{driver.label}</span><span className="font-mono text-[#00D4FF]">{driver.observation}</span></div>
                  <p className="mt-1 text-[#8FA8B8]"><span className="text-[#EAF4F8]">Meaning:</span> {driver.meaning}</p>
                  <p className="mt-1 text-[#18C7A0]"><span className="text-[#EAF4F8]">Decision effect:</span> {driver.effect}</p>
                </div>)}
              </div>
              {explainability.physics?.length > 0 && <details className="mt-3 rounded border border-[#20384D] bg-[#07111F]/50 p-2 text-xs text-[#8FA8B8]"><summary className="cursor-pointer font-semibold uppercase tracking-wider text-[#00D4FF]">Deterministic BSI physics trace</summary><div className="mt-2 space-y-2">{explainability.physics.map((factor, index) => <p key={`${factor.label}-${index}`}><span className="font-medium text-[#EAF4F8]">{factor.label} ({factor.observation}):</span> {factor.meaning} <span className="text-[#18C7A0]">{factor.effect}</span></p>)}</div></details>}
              {explainability.safeguards?.length > 0 && <div className="mt-3 space-y-1.5 border-t border-[#20384D] pt-2">{explainability.safeguards.map((item, index) => <p key={`${item.label}-${index}`} className="text-xs text-[#FFB547]"><span className="font-medium text-[#EAF4F8]">{item.label} · {item.state}:</span> {item.meaning} {item.effect}</p>)}</div>}
            </section>}</details>}
            {sourceStatuses.length > 0 && <section className="rounded-lg border border-[#20384D]/70 bg-[#07111F]/45 p-3" aria-label="Evidence freshness">
              <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#8FA8B8]">Evidence freshness</h4>
              <div className="mt-2 flex flex-wrap gap-1.5">{sourceStatuses.map((source, index) => <span key={`${source.source}-${index}`} title={source.reason || ''} className={`rounded border px-2 py-1 font-mono text-[10px] ${source.state === 'LIVE' ? 'border-[#18C7A0]/35 bg-[#18C7A0]/10 text-[#18C7A0]' : source.state === 'UNAVAILABLE' ? 'border-[#FFB547]/35 bg-[#FFB547]/10 text-[#FFB547]' : 'border-[#20384D] bg-[#13263A] text-[#8FA8B8]'}`}>{source.source} · {source.state}{source.cacheAgeSeconds != null ? ` · ${Math.round(source.cacheAgeSeconds / 60)}m` : ''}</span>)}</div>
            </section>}
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
            {ragFootnotes.map((note, idx) => {
              const href = citationHref(note);
              const content = <><span className="mr-1.5 opacity-70">📄</span>{citationLabel(note)}</>;
              return href ? <a key={idx} href={href} target="_blank" rel="noreferrer" className="inline-flex items-center px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] text-[#00D4FF] hover:bg-white/10 transition-colors">{content}</a> : <span key={idx} className="inline-flex items-center px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] text-[#00D4FF]">{content}</span>;
            })}
          </div>
        </div>
      )}

      {/* Action Tray (Dynamic Follow-ups) */}
      {followups && followups.length > 0 && (
        <div className="px-6 py-4 bg-white/[0.02] border-t border-white/10 flex flex-wrap gap-2">
          {canRouteToPfz && (
            <button
              type="button"
              onClick={() => onRouteToPfz && onRouteToPfz()}
              className="px-4 py-2 bg-[#00D4FF]/10 hover:bg-[#00D4FF]/20 border border-[#00D4FF]/55 hover:border-[#00D4FF] rounded-lg text-xs font-medium text-[#EAF4F8] transition-all duration-300 flex items-center space-x-2"
            >
              <span className="text-[#00D4FF]">↗</span>
              <span>Route to this verified PFZ</span>
            </button>
          )}
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
