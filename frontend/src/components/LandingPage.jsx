import React, { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowUpRight, Compass, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const STORY_MARKERS = ['Earth', 'Morning', 'Questions', 'People', 'NAVIK', 'Vision'];
const PERSPECTIVES = [
  { image: '/landing/fisherman-decision.jpeg', eyebrow: 'For the person who goes to sea', question: 'Where should I fish today?', answer: 'A better day begins with a clearer view of where the sea is most promising.' },
  { image: '/landing/coastal-authority.jpeg', eyebrow: 'For the people watching the coast', question: 'What should we prepare for?', answer: 'Changing conditions are easier to act on when they can be understood together.' },
  { image: '/landing/marine-researcher.jpeg', eyebrow: 'For the people studying change', question: 'What is happening beneath the surface?', answer: 'Observations become more meaningful when they reveal the pattern, not just the reading.' }
];

export default function LandingPage({ onLaunchConsole }) {
  const navigate = useNavigate();
  const [activeMarker, setActiveMarker] = useState(0);
  const [heroReady, setHeroReady] = useState(false);
  const sceneRefs = useRef([]);

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return undefined;
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible?.target?.dataset.marker) setActiveMarker(Number(visible.target.dataset.marker));
    }, { threshold: [0.35, 0.6, 0.85] });
    sceneRefs.current.forEach((scene) => scene && observer.observe(scene));
    return () => observer.disconnect();
  }, []);

  const registerScene = (index) => (element) => { sceneRefs.current[index] = element; };
  const openOperations = () => onLaunchConsole ? onLaunchConsole('routing') : navigate('/console/routing');
  const openIntelligence = () => navigate('/intelligence');

  return (
    <main className={`navik-story${heroReady ? ' is-ready' : ' is-loading'}`} aria-label="NAVIK marine intelligence story">
      <div className="navik-loader" role="status" aria-live="polite" aria-label="Preparing NAVIK ocean story"><span>NAVIK</span><i aria-hidden="true" /><small>Preparing the ocean view</small></div>
      <a className="navik-skip-link" href="#navik-reveal">Skip to NAVIK</a>
      <header className="navik-story__header">
        <a className="navik-brand" href="#the-ocean" aria-label="NAVIK story, back to beginning"><span className="navik-brand__mark" aria-hidden="true"><span /></span><span>NAVIK</span></a>
        <nav className="navik-progress" aria-label="Story progress">
          {STORY_MARKERS.map((marker, index) => <a key={marker} className={activeMarker === index ? 'is-active' : ''} href={`#scene-${index}`}><span>{String(index + 1).padStart(2, '0')}</span>{marker}</a>)}
        </nav>
      </header>

      <section id="the-ocean" ref={registerScene(0)} data-marker="0" className="navik-scene navik-scene--earth" aria-labelledby="earth-title">
        <img className="navik-scene__image" src="/landing/earth-indian-ocean.jpeg" alt="Earth at dawn, with the Indian Ocean and India in view." onLoad={() => setHeroReady(true)} onError={() => setHeroReady(true)} />
        <div className="navik-scene__shade" />
        <div className="navik-scene__content navik-scene__content--hero">
          <p className="navik-kicker">A story from the Indian Ocean</p><h1 id="earth-title">The ocean connects every coast.<br /><em>And it never stands still.</em></h1>
          <p className="navik-lede">A living system of wind, water, weather, and people making decisions before the day has begun.</p>
          <div className="navik-actions navik-actions--hero" aria-label="Explore NAVIK now"><button type="button" onClick={openOperations}><Compass size={17} aria-hidden="true" />Open Operations Console <ArrowUpRight size={17} aria-hidden="true" /></button><button type="button" className="navik-actions__secondary" onClick={openIntelligence}><Sparkles size={17} aria-hidden="true" />Open Intelligence Console <ArrowUpRight size={17} aria-hidden="true" /></button></div>
          <a className="navik-scroll-prompt" href="#scene-1">Follow the story <ArrowDown size={17} aria-hidden="true" /></a>
        </div>
      </section>

      <section id="scene-1" ref={registerScene(1)} data-marker="1" className="navik-scene navik-scene--dawn" aria-labelledby="dawn-title">
        <img className="navik-scene__image" src="/landing/hero-coast-dawn.jpeg" alt="A quiet Indian fishing harbour at dawn." /><div className="navik-scene__wash" />
        <div className="navik-scene__content navik-scene__content--dawn"><p className="navik-kicker">At first light</p><h2 id="dawn-title">Before the boat leaves,<br />the ocean has already changed.</h2><p className="navik-lede">The tide has moved. The wind has turned. Conditions offshore are becoming tomorrow’s catch, today’s journey, and everyone’s responsibility.</p></div>
      </section>

      <section id="scene-2" ref={registerScene(2)} data-marker="2" className="navik-scene navik-scene--safety" aria-labelledby="safety-title">
        <img className="navik-scene__image" src="/landing/safe-departure.jpeg" alt="A fisher looking out at a roughening sea beneath heavy clouds." /><div className="navik-scene__shade navik-scene__shade--cool" />
        <div className="navik-scene__content navik-scene__content--safety"><p className="navik-kicker">One question before departure</p><h2 id="safety-title">Will it be safe<br />to go out this morning?</h2><p className="navik-lede">For coastal communities, information only matters when it arrives as an answer that can be used.</p></div>
      </section>

      <section id="scene-3" ref={registerScene(3)} data-marker="3" className="navik-stakes" aria-labelledby="stakes-title">
        <div className="navik-stakes__intro"><p className="navik-kicker">The human stakes</p><h2 id="stakes-title">One sea.<br /><em>Many reasons to understand it.</em></h2><p>For a fisher, it is a livelihood. For a coastal authority, it is a responsibility. For a researcher, it is a living system still revealing itself.</p></div>
        <div className="navik-perspectives">
          {PERSPECTIVES.map((perspective, index) => <article className="navik-perspective" key={perspective.question}><div className="navik-perspective__image-wrap"><img src={perspective.image} alt={perspective.question} /></div><div className="navik-perspective__copy"><p className="navik-perspective__eyebrow">0{index + 1} — {perspective.eyebrow}</p><h3>{perspective.question}</h3><p>{perspective.answer}</p></div></article>)}
        </div>
      </section>

      <section className="navik-decision" aria-labelledby="decision-title">
        <div className="navik-decision__question"><p className="navik-kicker">A decision moment</p><h2 id="decision-title">“Is it safe to go out<br /><em>tomorrow morning?”</em></h2><p>One plain question. No oceanographer’s vocabulary required.</p></div>
        <div className="navik-decision__field" aria-label="The information NAVIK brings together">
          <div className="navik-decision__signal"><span>01</span><strong>Wind</strong><i /></div><div className="navik-decision__signal"><span>02</span><strong>Waves</strong><i /></div><div className="navik-decision__signal"><span>03</span><strong>Currents</strong><i /></div><div className="navik-decision__signal"><span>04</span><strong>Location</strong><i /></div>
          <div className="navik-decision__answer"><span>What NAVIK does</span><strong>Brings the right marine evidence<br />into one clear next step.</strong><p>It never replaces judgment. It makes the conditions easier to understand.</p></div>
        </div>
      </section>

      <section id="scene-4" ref={registerScene(4)} data-marker="4" className="navik-understanding" aria-labelledby="understanding-title">
        <div className="navik-current-field" aria-hidden="true"><i /><i /><i /><i /><i /><b /><b /><b /><b /><b /><b /></div>
        <div className="navik-understanding__content"><p className="navik-kicker">From observation to understanding</p><h2 id="understanding-title">The ocean is not short of data.<br /><em>It is short of understanding.</em></h2><p>Weather, waves, currents, satellite observations, and local knowledge are all signals. NAVIK brings them into a picture people can use.</p><div className="navik-flow" aria-label="Observation, understanding, decision"><span>Observation</span><i aria-hidden="true" /><span>Understanding</span><i aria-hidden="true" /><strong>Decision</strong></div></div>
      </section>

      <section id="navik-reveal" className="navik-reveal" aria-labelledby="navik-title">
        <div className="navik-reveal__signal" aria-hidden="true"><span /><span /><span /></div><p className="navik-kicker">Introducing NAVIK</p><h2 id="navik-title">A clearer way to read<br /><em>the living ocean.</em></h2><p>NAVIK turns changing marine conditions into practical guidance for the people who need to make the next decision.</p>
        <div className="navik-actions" aria-label="Explore NAVIK"><button type="button" onClick={openOperations}><Compass size={17} aria-hidden="true" />Open Operations Console <ArrowUpRight size={17} aria-hidden="true" /></button><button type="button" className="navik-actions__secondary" onClick={openIntelligence}><Sparkles size={17} aria-hidden="true" />Open Intelligence Console <ArrowUpRight size={17} aria-hidden="true" /></button></div>
      </section>

      <section className="navik-outcomes" aria-labelledby="outcomes-title">
        <div><p className="navik-kicker">What a clearer ocean makes possible</p><h2 id="outcomes-title">Four ways NAVIK<br /><em>turns understanding into action.</em></h2></div>
        <div className="navik-outcomes__list">
          <article><span>01</span><h3>Find</h3><p>Better fishing opportunities.</p></article><article><span>02</span><h3>Protect</h3><p>Safer departure decisions.</p></article><article><span>03</span><h3>Navigate</h3><p>Clearer routes at sea.</p></article><article><span>04</span><h3>Discover</h3><p>Deeper marine understanding.</p></article>
        </div>
      </section>

      <section id="scene-5" ref={registerScene(5)} data-marker="5" className="navik-scene navik-scene--closing" aria-labelledby="closing-title">
        <img className="navik-scene__image" src="/landing/earth-indian-ocean.jpeg" alt="Earth seen from space as the sun rises over the Indian Ocean." /><div className="navik-scene__shade navik-scene__shade--closing" />
        <div className="navik-scene__content navik-scene__content--closing"><p className="navik-kicker">NAVIK</p><h2 id="closing-title">Intelligence<br /><em>for the living ocean.</em></h2><p className="navik-lede">From the coast to the open sea, clearer decisions begin with a deeper understanding.</p><div className="navik-actions navik-actions--closing" aria-label="Explore NAVIK"><button type="button" onClick={openOperations}><Compass size={17} aria-hidden="true" />Open Operations Console <ArrowUpRight size={17} aria-hidden="true" /></button><button type="button" className="navik-actions__secondary" onClick={openIntelligence}><Sparkles size={17} aria-hidden="true" />Open Intelligence Console <ArrowUpRight size={17} aria-hidden="true" /></button></div></div>
      </section>
    </main>
  );
}
