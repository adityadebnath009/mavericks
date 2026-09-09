import React from 'react';

const OrchestrationHUD = ({ events = [] }) => {
  if (!events || events.length === 0) return null;

  return (
    <div className="z-50">
      <div className="bg-[#07111F]/92 backdrop-blur-sm border border-[#20384D] p-4 rounded-xl shadow-xl min-w-[280px]">
        <h3 className="text-[#00D4FF] text-xs uppercase font-mono tracking-widest mb-4 flex items-center border-b border-[#20384D] pb-2">
          <svg className="w-4 h-4 mr-2 animate-spin-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          System Orchestration
        </h3>
        
        <div className="space-y-2 font-mono text-sm">
          {events.map((event, idx) => event && (
            <div key={idx} className="flex items-start">
              <span className={`mr-3 mt-0.5 ${event.status === 'pending' ? 'text-[#00D4FF] animate-pulse' : event.status === 'queued' ? 'text-[#8FA8B8]' : 'text-[#18C7A0]'}`}>
                {event.status === 'pending' ? '[~]' : event.status === 'queued' ? '[·]' : '[+]'}
              </span>
              <span className={`transition-all duration-300 ${event.status === 'pending' ? 'text-[#EAF4F8]' : 'text-[#8FA8B8]'}`}>
                {event.text}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OrchestrationHUD;
