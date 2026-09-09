import React from 'react';

const pathFor = (rows, field, width = 280, height = 72) => {
  const points = rows.map((row, index) => ({ index, value: Number(row[field]) })).filter((point) => Number.isFinite(point.value));
  if (!points.length) return null;
  const low = Math.min(...points.map((point) => point.value));
  const high = Math.max(...points.map((point) => point.value));
  const span = high - low || 1;
  return points.map((point, position) => {
    const x = points.length === 1 ? width / 2 : (position / (points.length - 1)) * width;
    const y = height - ((point.value - low) / span) * height;
    return `${position ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
};

const format = (value, digits = 3) => Number.isFinite(value) ? value.toFixed(digits) : 'Unavailable';

export default function ResearchTrendChart({ series = [], analysis = {}, papers = [] }) {
  const hasSeries = Array.isArray(series) && series.length > 0;
  const hasPapers = Array.isArray(papers) && papers.length > 0;
  if (!hasSeries && !hasPapers) return null;
  const sstPath = pathFor(series, 'sstC');
  const chlorophyllPath = pathFor(series, 'chlorophyllMgM3');
  return (
    <section className="mt-3 max-w-2xl rounded-xl border border-[#20384D]/70 bg-[#07111F]/90 p-3 shadow-xl backdrop-blur-sm" aria-label="Authenticated GEE historical trend chart">
      {hasSeries ? <><div className="flex items-baseline justify-between gap-3"><h2 className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#00D4FF]">GEE historical trend</h2><span className="text-[10px] text-[#8FA8B8]">Annual means · {analysis.observations || series.length} observations</span></div>
      <svg className="mt-2 h-[74px] w-full" viewBox="0 0 280 72" role="img" aria-label="SST and chlorophyll annual trends"><path d="M0 71 H280" stroke="#20384D" strokeWidth="1" />{sstPath && <path d={sstPath} fill="none" stroke="#FFB547" strokeWidth="2.5" />}{chlorophyllPath && <path d={chlorophyllPath} fill="none" stroke="#18C7A0" strokeWidth="2.5" />}</svg>
      <div className="grid gap-1 text-[10px] text-[#8FA8B8] sm:grid-cols-3"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#FFB547]" />SST {format(analysis.sstTrendCPerYear)}°C/yr</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#18C7A0]" />Chl {format(analysis.chlorophyllTrendMgM3PerYear)} mg/m³/yr</span><span>Correlation r={format(analysis.sstChlorophyllCorrelation, 2)} · not causation</span></div></> : <p className="text-xs text-[#8FA8B8]">GEE historical trend is unavailable; literature evidence remains available.</p>}
      {hasPapers && <div className="mt-3 border-t border-[#20384D]/70 pt-3">
        <h3 className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#00D4FF]">Scholarly literature evidence</h3>
        <ul className="mt-2 space-y-2">
          {papers.slice(0, 4).map((paper, index) => {
            const href = paper.landingPageUrl || paper.doi || paper.id;
            const title = paper.title || 'Untitled work';
            return <li key={paper.id || `${title}-${index}`} className="rounded-md border border-[#20384D]/60 bg-[#07111F]/55 px-2 py-1.5 text-xs text-[#EAF4F8]">
              {href ? <a href={href} target="_blank" rel="noreferrer" className="font-medium text-[#00D4FF] hover:underline">{title}</a> : <span className="font-medium">{title}</span>}
              <p className="mt-0.5 text-[10px] text-[#8FA8B8]">{[paper.publicationDate, paper.source, paper.citationCount != null ? `${paper.citationCount} citations` : null, paper.sources?.join(' + ')].filter(Boolean).join(' · ') || 'Indexed scholarly work'}</p>
            </li>;
          })}
        </ul>
      </div>}
    </section>
  );
}
