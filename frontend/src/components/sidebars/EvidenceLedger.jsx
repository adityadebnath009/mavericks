import React from 'react';

const getStatusColor = (assessment) => {
  switch (assessment?.toUpperCase()) {
    case 'SAFE':
      return 'text-[#18C7A0]'; // Sea Green
    case 'UNSAFE':
      return 'text-[#FF5C5C]'; // Coral Red
    default:
      return 'text-[#FFB547]'; // Amber
  }
};

const EvidenceLedger = ({
  evidenceMet = 0,
  evidenceRequired = 0,
  assessment = 'UNKNOWN',
  certification = 'PENDING',
  sources = []
}) => {
  const percentage = evidenceRequired > 0 ? (evidenceMet / evidenceRequired) * 100 : 0;
  const statusColor = getStatusColor(assessment);

  return (
    <div className="flex flex-col bg-[#0D1B2A] border border-[#20384D] rounded-lg p-4 w-72 h-full text-[#EAF4F8] shadow-xl">
      <h2 className="text-[#8FA8B8] text-xs uppercase font-bold tracking-widest mb-4 border-b border-[#20384D] pb-2">
        Evidence Ledger
      </h2>

      {/* Validation Section */}
      <div className="mb-6">
        <h3 className="text-[#8FA8B8] text-[10px] uppercase font-semibold mb-2 tracking-wider">Validation</h3>
        <div className="w-full bg-[#07111F] rounded-full h-2 mb-1 border border-[#20384D]">
          <div
            className="bg-[#00D4FF] h-full rounded-full transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className="text-right text-xs font-mono text-[#00D4FF]">
          {evidenceMet} / {evidenceRequired}
        </div>
      </div>

      {/* Assessment Section */}
      <div className="mb-6">
        <h3 className="text-[#8FA8B8] text-[10px] uppercase font-semibold mb-2 tracking-wider">Assessment</h3>
        <div className="flex items-center space-x-2 bg-[#07111F] px-3 py-2 rounded border border-[#20384D]">
          <div className={`w-2 h-2 rounded-full bg-current ${statusColor} animate-pulse`} />
          <span className={`font-mono text-sm font-bold ${statusColor}`}>{assessment}</span>
        </div>
      </div>

      {/* Certification Section */}
      <div className="mb-6">
        <h3 className="text-[#8FA8B8] text-[10px] uppercase font-semibold mb-2 tracking-wider">Certification</h3>
        <div className="flex items-center space-x-2 bg-[#07111F] px-3 py-2 rounded border border-[#20384D]">
          {certification === 'VALID' ? (
            <svg className="w-4 h-4 text-[#18C7A0]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
          ) : (
            <svg className="w-4 h-4 text-[#FFB547]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          )}
          <span className={`font-mono text-sm font-bold ${certification === 'VALID' ? 'text-[#18C7A0]' : 'text-[#FFB547]'}`}>
            {certification}
          </span>
        </div>
      </div>

      {/* Sources Section */}
      <div className="mt-auto">
        <h3 className="text-[#8FA8B8] text-[10px] uppercase font-semibold mb-2 tracking-wider">Sources</h3>
        <div className="space-y-2">
          {sources.map((source, idx) => (
            <div key={idx} className="flex items-center space-x-2 bg-[#07111F] px-2 py-1.5 rounded border border-[#20384D] text-xs cursor-pointer hover:border-[#00D4FF] hover:bg-[#13263A] transition-colors">
              <span className="text-[#8FA8B8] opacity-70">
                {source.includes('GEE') ? '🛰' : source.includes('INCOIS') ? '🌊' : source.includes('Meteo') ? '🌦' : '📄'}
              </span>
              <span className="font-medium text-[#EAF4F8] truncate">{source}</span>
            </div>
          ))}
          {sources.length === 0 && (
            <div className="text-xs text-[#8FA8B8] italic opacity-50">No external sources</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EvidenceLedger;
