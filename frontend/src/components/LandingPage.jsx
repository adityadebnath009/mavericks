import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Compass, 
  Waves, 
  Wind, 
  Cpu, 
  Radio, 
  Layers, 
  Database, 
  FileText, 
  Mic, 
  Volume2, 
  MapPin, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  Navigation, 
  Activity, 
  Lock, 
  Sparkles, 
  Server, 
  Code2, 
  Anchor,
  HelpCircle,
  X,
  Play,
  Square
} from 'lucide-react';
import TacticalGlobe from './TacticalGlobe';

// 9 Specialized AI Agents Data & Technical Specs
const AGENT_SPECIFICATIONS = [
  {
    id: 'agent-01',
    num: '01',
    name: 'User Interaction Agent',
    role: 'Front-End Liaison & Multilingual Vocalist',
    icon: Mic,
    color: '#00D4FF',
    status: 'ACTIVE // LISTENING',
    inputs: 'Browser Web Speech API, Localized Speech-to-Text (STT)',
    outputs: 'Vocal syntheses (TTS) & UI state in English, Hindi (हिन्दी), Marathi (मराठी)',
    tech: 'Web Speech API, Multi-turn Dialogue State Tracker',
    description: 'Captures voice queries directly in the browser with zero external speech API cost. Synthesizes spoken advisory responses in regional fishing languages.'
  },
  {
    id: 'agent-02',
    num: '02',
    name: 'Planner Agent',
    role: 'Coordinator & Failsafe Resilience Guard',
    icon: Cpu,
    color: '#00D4FF',
    status: 'ORCHESTRATING',
    inputs: 'Decoded user query, departure timestamp, vessel beam width',
    outputs: 'Asynchronous DAG execution sequence & failover fallback triggers',
    tech: 'Stateful Orchestrator Pattern, Failsafe State Machine',
    description: 'Decomposes complex requests into concurrent sub-tasks. If PostGIS drops or INCOIS times out, it automatically shifts downstream execution to local SQLite/JSON caches.'
  },
  {
    id: 'agent-03',
    num: '03',
    name: 'Marine Data Discovery Agent',
    role: 'Honest Scientific Provider Interface',
    icon: Database,
    color: '#18C7A0',
    status: 'SYNCED (0.4° GRID)',
    inputs: 'INCOIS OPeNDAP THREDDS catalog, Open-Meteo services',
    outputs: 'Slices NetCDF arrays (Hs, T02, Wind, Currents) via xarray',
    tech: 'xarray, THREDDS OPeNDAP, ISRO MOSDAC Adapter',
    description: 'Wraps telemetry endpoints behind an interchangeable interface, enabling development Open-Meteo feeds to swap with ISRO MOSDAC / INCOIS feeds seamlessly.'
  },
  {
    id: 'agent-04',
    num: '04',
    name: 'Weather Intelligence Agent',
    role: 'Meteorological Hazard & Wave Analyzer',
    icon: Wind,
    color: '#FFB547',
    status: 'ANALYZING',
    inputs: 'WaveWatch III grids, IMD RSMC weather bulletins',
    outputs: 'SVAS Boat Safety Index (BSI), crossing sea & wave steepness flags',
    tech: 'SVAS BSI Calculator, Crossing Sea Detection Vector',
    description: 'Calculates directional wave spread, steepness indices, and wind gusts to identify marine depressions and squall lines along planned tracks.'
  },
  {
    id: 'agent-05',
    num: '05',
    name: 'Ocean Analytics Agent',
    role: 'Oceanographic & PFZ Potential Analyst',
    icon: Waves,
    color: '#18C7A0',
    status: 'ACTIVE // PFZ-17',
    inputs: 'SST rasters, Chlorophyll-a gradients, INCOIS WFS contours',
    outputs: 'Potential Fishing Zone coordinates & thermal fronts',
    tech: 'SST Gradient Filter, Chlorophyll-a Optical Slicer',
    description: 'Detects thermal front boundaries and chlorophyll convergence lines to identify high-yield Potential Fishing Zones (PFZs).'
  },
  {
    id: 'agent-06',
    num: '06',
    name: 'Geospatial Reasoning Agent',
    role: 'PostGIS Spatial Engine & Boundary Guard',
    icon: MapPin,
    color: '#FF5C5C',
    status: 'GEOFENCE ENFORCED',
    inputs: 'Vessel coordinates, india_eez & marine_protected_areas tables',
    outputs: 'ST_Contains checks, distance-to-border, MPA intrusion alerts',
    tech: 'PostGIS (Neon DB), ST_Distance, Vector Drift Geofencing',
    description: 'Executes sub-millisecond spatial queries against international maritime borders and eco-sanctuaries, generating proactive 5 km buffer alerts.'
  },
  {
    id: 'agent-07',
    num: '07',
    name: 'Risk Assessment Agent',
    role: 'XGBoost ML Classifier + Deterministic Floors',
    icon: Shield,
    color: '#FFB547',
    status: 'FLOORS ARMED',
    inputs: 'Interpolated path metrics, vessel beam width, distance to coast',
    outputs: 'Calibrated Risk Score (LOW to EXTREME) + Confidence Level',
    tech: 'XGBoost Classifier, Deterministic Safety Floor Overrides',
    description: 'Combines statistical ML classification with hard deterministic safety floors (e.g. waves >= 4m force score 85, Cyclone warning forces 92) for mathematical safety.'
  },
  {
    id: 'agent-08',
    num: '08',
    name: 'Visualization Agent',
    role: 'Tactical UI Asset & Vector Map Builder',
    icon: Layers,
    color: '#00D4FF',
    status: 'RENDERING',
    inputs: 'Waypoints array, calculated risk grids, boundary polygons',
    outputs: 'MapLibre GL GeoJSON FeatureCollections & Recharts 24h timelines',
    tech: 'MapLibre GL JS, GeoJSON Engine, Recharts SVGs',
    description: 'Transforms raw numerical coordinates into high-contrast naval tactical map layers, route vectors, and 24-hour diurnal risk charts.'
  },
  {
    id: 'agent-09',
    num: '09',
    name: 'Reporting Agent',
    role: 'Grounded RAG Compliance Compiler',
    icon: FileText,
    color: '#18C7A0',
    status: 'pgvector READY',
    inputs: 'Calculated risk parameters, FAO small craft manuals, Coast Guard codes',
    outputs: 'Plain-language advisory with verifiable legal & safety citations',
    tech: 'pgvector (Neon DB), BGE-M3 Embeddings, Gemini Flash RAG',
    description: 'Performs semantic vector searches against official maritime regulations, ensuring all safety advisories provide cited, explainable rationale rather than a black box.'
  }
];

// How Navik Thinks: Step-by-Step User Journey
const USER_JOURNEY_STEPS = [
  {
    step: '01',
    phase: 'ASK',
    title: 'Natural Language Query',
    tag: 'VOICE OR TEXT',
    quote: '"Is it safe to go from Kochi to Lakshadweep leaving tomorrow morning?"',
    actor: 'User Interaction Agent',
    detail: 'Captured natively via browser Web Speech API in English, Hindi (हिन्दी), or Marathi (मराठी). No proprietary voice vendor lock-in.',
    outputLabel: 'Intent Payload',
    outputVal: '{ origin: "Kochi", dest: "Lakshadweep", depart: "2026-08-29T06:00Z", beam: 3.5m }'
  },
  {
    step: '02',
    phase: 'UNDERSTAND',
    title: 'Intent Extraction & Task Graph',
    tag: 'TASK DECOMPOSITION',
    quote: 'Decomposing query parameters, temporal departure window, and vessel stability limits.',
    actor: 'Planner Agent',
    detail: 'Extracts spatial waypoints, planned departure timestamps, and vessel beam constraints. Initializes concurrent sub-agent dispatch.',
    outputLabel: 'Execution DAG',
    outputVal: '3 Concurrent Pipelines: [Telemetry Discovery, PostGIS Geofence, Weather Hazard]'
  },
  {
    step: '03',
    phase: 'ANALYZE',
    title: 'Multi-Source Scientific Slicing',
    tag: 'DATA FUSION',
    quote: 'Interpolating WaveWatch III grids, ocean current velocities, and PostGIS boundary layers.',
    actor: 'Weather & Ocean Intelligence Agents',
    detail: 'Fetches 24-hour diurnal timelines for wave height (Hs), peak period, surface current vectors, and queries PostGIS boundaries for active MPAs.',
    outputLabel: 'Spatial Grid',
    outputVal: '0.4° Resolution NetCDF Array (Hs: 1.2m, Current: 0.35m/s, Wind: 18.5 km/h)'
  },
  {
    step: '04',
    phase: 'OPTIMIZE',
    title: 'Current-Aware Vector Routing',
    tag: 'PATHFINDING',
    quote: 'Dijkstra pathfinder calculating current drift projection (Vc · cos Δθ) avoiding MPAs.',
    actor: 'Geospatial & Risk Agents',
    detail: 'Calculates optimal waypoint transitions across a 0.4° grid. Steers clear of restricted eco-zones while riding favorable surface current vectors.',
    outputLabel: 'Optimal Vector',
    outputVal: '215 NM Arc (+18% Fuel Efficiency, Wave Steepness 0.012 within safe limits)'
  },
  {
    step: '05',
    phase: 'ADVISE',
    title: 'Explainable Grounded Advisory',
    tag: 'GROUNDED RAG & SPEECH',
    quote: '"Safe to venture into sea. Departure recommended at 06:00 UTC. CMFRI Guideline Clause 4.2 cited."',
    actor: 'Reporting & Visualization Agents',
    detail: 'Renders the route on the MapLibre tactical canvas, displays 24h Recharts trends, and vocalizes the safety verdict quoting official maritime safety codes.',
    outputLabel: 'Advisory Verdict',
    outputVal: 'RATING: SAFE // DEPARTURE WINDOW: +2H // REGULATORY CITATION: FAO-CMFRI-2024'
  }
];

// Core Capabilities Matrix
const CAPABILITY_CARDS = [
  {
    icon: Shield,
    title: 'Marine Risk Predictor',
    category: 'ML + DETERMINISTIC FLOORS',
    color: '#FFB547',
    summary: 'Machine learning safety classifier combined with mathematical safety floor overrides.',
    points: [
      'XGBoost trained on temporal split ocean datasets.',
      'Deterministic floors: Waves >= 4m force score 85.',
      'Cyclone alerts mathematically enforce rating 92.'
    ]
  },
  {
    icon: Navigation,
    title: 'Safe-Route Optimization',
    category: 'VECTOR PATHFINDING',
    color: '#00D4FF',
    summary: 'Current-aware Dijkstra pathfinding saving fuel while steering around restricted MPAs.',
    points: [
      'Projects surface current drift speed (Vc · cos Δθ).',
      'Calculates diurnal safety departure windows (+2h, +4h).',
      'Dynamically interpolates arrival times at each waypoint.'
    ]
  },
  {
    icon: MapPin,
    title: 'Geofencing & Borders',
    category: 'POSTGIS SPATIAL ENGINE',
    color: '#FF5C5C',
    summary: 'Sub-millisecond spatial queries checking Indian EEZ and Marine Protected Area boundaries.',
    points: [
      'ST_Contains and ST_Distance PostGIS lookups.',
      '5.0 km predictive buffer warning on vessel vector drift.',
      'Protects vessels from international boundary crossings.'
    ]
  },
  {
    icon: FileText,
    title: 'Grounded Safety Advisor',
    category: 'PGVECTOR RAG COMPLIANCE',
    color: '#18C7A0',
    summary: 'Semantic vector retrieval quoting official maritime manuals rather than a black box.',
    points: [
      'pgvector index with BGE-M3 dense embeddings.',
      'Cites FAO small craft manuals and Coast Guard codes.',
      'Multi-turn conversational memory with explainable logic.'
    ]
  },
  {
    icon: Mic,
    title: 'Multilingual Voice Outreach',
    category: 'WEB SPEECH API',
    color: '#00D4FF',
    summary: 'Zero-cost client-side speech recognition and vocal read-back in coastal languages.',
    points: [
      'Native browser Speech-to-Text (STT) integration.',
      'Audio synthesis (TTS) in English, Hindi, and Marathi.',
      'Zero external cloud API subscription overhead.'
    ]
  },
  {
    icon: Server,
    title: 'Offline-First Resilience',
    category: 'FAILSAFE MIDDLEWARE',
    color: '#18C7A0',
    summary: 'Automatic switchover to local SQLite and pre-cached JSONs if remote servers drop.',
    points: [
      'Middleware intercepts database/network timeouts.',
      'Seamless fallback to static JSON forecast timelines.',
      'SQLite backup for spatial boundaries prevents app crashes.'
    ]
  }
];

// Live Telemetry Ticker Items
const TELEMETRY_FEED = [
  { type: 'SYS', color: '#18C7A0', text: 'INCOIS GeoServer & OPeNDAP proxy ONLINE // 0.4° resolution diurnal grid synchronized.' },
  { type: 'GEO', color: '#00D4FF', text: 'Vessel Sagar Kanya updated coordinates (17.43°N, 84.70°E). EEZ buffer clear: 116.9 km.' },
  { type: 'WARN', color: '#FFB547', text: 'Significant wave height warning (Hs >= 3.5m) in Gujarat Coastline. Small craft advisory.' },
  { type: 'RISK', color: '#FF5C5C', text: 'Deterministic safety floor active in Sector-4 due to IMD Squally Weather bulletin.' },
  { type: 'RAG', color: '#00D4FF', text: 'pgvector semantic index primed: 1,420 regulatory safety clauses embedded.' },
  { type: 'FLEET', color: '#18C7A0', text: 'Active Simulation Fleet: 104 vessels operating within monitored EEZ sectors.' }
];

// Progressive FAQ List
const FAQ_ITEMS = [
  {
    id: 'faq-1',
    question: 'How does Navik predict safety risks without acting as a "black box"?',
    simple: 'Navik evaluates wind speeds, wave heights, and ocean currents through a trained machine learning model, but strictly overrides it with non-negotiable safety rules for extreme weather.',
    technical: `INGESTION & FEATURE PIPELINE:
• Ingests WaveWatch III NetCDF rasters (Hs, T02, MWD) and surface current grids.
• Calculates wave steepness (Hs / (1.56 * T02^2)) and SVAS Boat Safety Index (BSI 0-7).
• Evaluates XGBoost Classifier calibrated on historical marine safety datasets.

DETERMINISTIC SAFETY FLOORS:
• If IMD Squall/Cyclone warning active ➔ Risk score forced to >= 92 (EXTREME).
• If Significant Wave Height (Hs) >= 4.0m ➔ Risk score forced to >= 85 (HIGH).
• If vessel beam < 4m and wave steepness > 0.04 ➔ Risk score forced to >= 70 (MODERATE).`
  },
  {
    id: 'faq-2',
    question: 'How does the pathfinder calculate safe routes around restricted zones and ocean currents?',
    simple: 'It uses a specialized navigation algorithm that navigates along favorable ocean currents to conserve fuel while mathematically preventing the vessel from entering marine protected areas.',
    technical: `PATHFINDING & CURRENT PROJECTION:
• Constructs a 0.4° spatial graph over the Indian EEZ polygon boundaries.
• Prunes nodes intersecting PostGIS 'marine_protected_areas' via ST_Intersects.
• Projects surface current velocity (Vc) onto ship heading angle (θ):
    Effective Speed = V_vessel + (V_current * cos(Δθ))
• Executes Dijkstra algorithm with dynamic edge weights factoring fuel savings and wave steepness penalties.
• Calculates ETA at intermediate waypoints to dynamically fetch temporal weather slices.`
  },
  {
    id: 'faq-3',
    question: 'What happens if the remote database or weather server drops offline at sea?',
    simple: 'Navik includes an automatic offline-first fallback system that switches to local database records and pre-cached files without ever crashing the app.',
    technical: `FAILSAFE ARCHITECTURE:
• FastAPI middleware wraps all database session executions with 2.5s circuit breakers.
• On Neon PostgreSQL timeout: Downstream queries route to local SQLite3 spatial boundary tables.
• On remote OPeNDAP timeout: Planner retrieves pre-warmed static JSON files ('safety_grid_day_d_hour_h.json').
• Client-side React state gracefully renders cached provenance metadata with timestamp indicators.`
  },
  {
    id: 'faq-4',
    question: 'How is regulatory compliance guaranteed in AI Safety Advisories?',
    simple: 'Every spoken and written advisory retrieves verbatim paragraphs from official maritime manuals (such as CMFRI, FAO, and Indian Coast Guard safety guidelines) using semantic search.',
    technical: `GROUNDED RAG COMPLIANCE PIPELINE:
• Safety manuals embedded using BGE-M3 dense embeddings into Neon PostgreSQL 'pgvector' table.
• Risk factors (wave height, beam vulnerability) form the search query vector.
• Cosine distance search extracts top-k regulatory clauses with confidence thresholds >= 0.82.
• Advisories quote specific clause numbers (e.g. CMFRI Guideline 4.2) to eliminate hallucination.`
  },
  {
    id: 'faq-5',
    question: 'How does Navik support non-English speaking coastal fishermen?',
    simple: 'Navik runs speech recognition and voice read-backs directly inside the fisherman’s web browser in English, Hindi, and Marathi with zero lag and zero subscription fees.',
    technical: `CLIENT-SIDE SPEECH ARCHITECTURE:
• Utilizes native browser Web Speech API (webkitSpeechRecognition) with localized grammar prompts.
• Locales supported: 'en-IN' (English), 'hi-IN' (हिन्दी), 'mr-IN' (मराठी).
• Natural language text passed to Planner Agent for coordinate entity resolution.
• Generated advisory synthesized via window.speechSynthesis with regional phonetic dictionaries.`
  }
];

// Multilingual Advisory Samples for Web Speech testing
const ADVISORY_SAMPLES = {
  en: {
    langName: 'English (Maritime)',
    code: 'en-IN',
    query: '"Is it safe to go from Kochi to Lakshadweep leaving tomorrow morning?"',
    spoken: 'Safe to venture into sea. Departure recommended at 06:00 UTC. Ocean current vectors favorable with 18% fuel efficiency bonus. Significant wave height is 1.2 meters, within safe operational limits. CMFRI Guideline Clause 4.2 cited.',
    display: 'RATING: SAFE // WINDOW: 06:00 - 12:00 UTC // MAX HS: 1.2M // CURRENT: 0.35 M/S SE',
    citation: 'FAO Small Craft Code §4.2 • CMFRI Advisory 2026-BSI-1'
  },
  hi: {
    langName: 'हिन्दी (Hindi)',
    code: 'hi-IN',
    query: '"क्या कल सुबह कोच्चि से लक्षद्वीप जाना सुरक्षित है?"',
    spoken: 'कल सुबह समुद्र में नौकायन सुरक्षित है। सुबह ०६:०० बजे प्रस्थान करने की सलाह दी जाती है। दोपहर १२ बजे से पहले लौटें क्योंकि हवा की गति में हल्की वृद्धि हो सकती है। लाटों की ऊंचाई १.२ मीटर है जो सुरक्षित सीमा में है।',
    display: 'स्थिति: सुरक्षित // प्रस्थान समय: ०६:०० UTC // अधिकतम तरंग: १.२ मीटर',
    citation: 'भारतीय तटरक्षक सुरक्षा नियम एवं CMFRI सलाह २०२६'
  },
  mr: {
    langName: 'मराठी (Marathi)',
    code: 'mr-IN',
    query: '"उद्या सकाळी कोचीहून लक्षद्वीपला जाणे सुरक्षित आहे का?"',
    spoken: 'उद्या सकाळी प्रवास करणे सुरक्षित आहे. सकाळी ०६:०० वाजता निघण्याची शिफारस आहे. समुद्रातील लाटा १.२ मीटर असून सुरक्षित मर्यादेत आहेत. दुपारी १२ च्या आत परत या.',
    display: 'स्थिती: सुरक्षित // प्रवासाची वेळ: ०६:०० UTC // लाटांची उंची: १.२ मी',
    citation: 'महाराष्ट्र मत्स्यव्यवसाय नियमावली व CMFRI कलम ४.२'
  }
};

export default function LandingPage({ onLaunchConsole }) {
  const [selectedAgentIndex, setSelectedAgentIndex] = useState(0);
  const [selectedJourneyStep, setSelectedJourneyStep] = useState(0);
  const [expandedFaqId, setExpandedFaqId] = useState('faq-1');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState({ 'faq-1': true });
  const [isAdvisorModalOpen, setIsAdvisorModalOpen] = useState(false);
  const [advisorLang, setAdvisorLang] = useState('en');
  const [isSpeaking, setIsSpeaking] = useState(false);

  const activeAgent = AGENT_SPECIFICATIONS[selectedAgentIndex];
  const activeJourney = USER_JOURNEY_STEPS[selectedJourneyStep];

  // Defensive cleanup for Web Speech API on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
        } catch (_) {}
      }
    };
  }, []);

  const toggleTechnical = (id) => {
    setShowTechnicalDetails(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleLaunch = (mode = 'map') => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (_) {}
    }
    setIsSpeaking(false);
    setIsAdvisorModalOpen(false);
    if (onLaunchConsole) {
      onLaunchConsole(mode);
    }
  };

  const playSpeechSample = (langKey) => {
    setAdvisorLang(langKey);
    const sample = ADVISORY_SAMPLES[langKey];
    if (!sample) return;

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(sample.spoken);
        utterance.lang = sample.code;
        utterance.rate = 0.92;
        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.warn('Speech synthesis playback exception:', e);
        setIsSpeaking(false);
      }
    } else {
      setIsSpeaking(true);
      setTimeout(() => setIsSpeaking(false), 3000);
    }
  };

  const stopSpeech = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (_) {}
    }
    setIsSpeaking(false);
  };

  const closeAdvisorModal = () => {
    stopSpeech();
    setIsAdvisorModalOpen(false);
  };

  return (
    <div className="w-full min-h-screen bg-[#07111F] text-[#EAF4F8] font-sans antialiased overflow-x-hidden selection:bg-[#00D4FF]/30 selection:text-[#EAF4F8]">
      
      {/* 1. Header Navigation Bar */}
      <header className="sticky top-0 z-50 h-16 bg-[#0D1B2A]/90 backdrop-blur-md border-b border-[#20384D] px-4 lg:px-8 flex items-center justify-between">
        {/* Brand Emblem */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-[#13263A] border border-[#20384D] shadow-inner">
            {/* Pulsing Radar Dot */}
            <div className="w-2.5 h-2.5 rounded-full bg-[#00D4FF] animate-ping opacity-75 absolute" />
            <div className="w-2 h-2 rounded-full bg-[#00D4FF]" />
            <div className="absolute inset-0 rounded-xl border border-[#00D4FF]/30" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold tracking-widest text-[#EAF4F8] uppercase font-mono">
                NAVIK
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-semibold">
                SIH26176
              </span>
            </div>
            <span className="text-[10px] text-[#8FA8B8] hidden sm:block">
              Intelligent Marine Decision-Support Platform
            </span>
          </div>
        </div>

        {/* Quick Links */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-mono text-[#8FA8B8]">
          <a href="#how-it-thinks" className="hover:text-[#00D4FF] transition-colors">01 // PROCESS</a>
          <a href="#agents-ecosystem" className="hover:text-[#00D4FF] transition-colors">02 // 9 AGENTS</a>
          <a href="#capabilities" className="hover:text-[#00D4FF] transition-colors">03 // CAPABILITIES</a>
          <a href="#telemetry" className="hover:text-[#00D4FF] transition-colors">04 // TELEMETRY</a>
          <a href="#faq" className="hover:text-[#00D4FF] transition-colors">05 // FAQ</a>
        </nav>

        {/* Header Action & Status */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#13263A] border border-[#20384D] text-[10px] font-mono text-[#18C7A0]">
            <div className="w-1.5 h-1.5 rounded-full bg-[#18C7A0] animate-pulse" />
            <span>SIMULATION FEED ACTIVE</span>
          </div>

          <button
            onClick={() => handleLaunch('map')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00D4FF] text-[#07111F] font-bold text-xs hover:bg-[#00D4FF]/90 transition-all shadow-[0_0_15px_rgba(0,212,255,0.25)] cursor-pointer"
          >
            <span>LAUNCH CONSOLE</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* 2. Hero Section (Split View - Above the Fold) */}
      <section className="relative pt-8 pb-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          
          {/* Left Column: Headline, CTAs, Telemetry */}
          <div className="lg:col-span-6 space-y-6">
            
            {/* Tactical Tag Chip */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-[#0D1B2A] border border-[#20384D] text-xs font-mono text-[#00D4FF]">
              <Radio className="w-3.5 h-3.5 animate-pulse text-[#00D4FF]" />
              <span>AUTONOMOUS MULTI-AGENT OCEAN INTELLIGENCE</span>
            </div>

            {/* Main Headline */}
            <div className="space-y-3">
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-[#EAF4F8] leading-tight">
                INTELLIGENT MARINE <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00D4FF] via-[#18C7A0] to-[#EAF4F8]">
                  DECISION-SUPPORT
                </span>
              </h1>
              <p className="text-sm sm:text-base text-[#8FA8B8] leading-relaxed max-w-xl">
                Plan safer, weather-aware maritime routes across dynamic ocean conditions. Coordinates 
                <span className="text-[#EAF4F8] font-semibold"> 9 specialized collaborative AI agents</span> to generate geofenced, current-optimized advisories with deterministic safety floors.
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={() => handleLaunch('map')}
                className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-[#00D4FF] text-[#07111F] font-extrabold text-sm hover:shadow-[0_0_25px_rgba(0,212,255,0.4)] transition-all cursor-pointer"
              >
                <Compass className="w-4 h-4" />
                <span>Launch Operations Console</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>

              <button
                onClick={() => {
                  setIsAdvisorModalOpen(true);
                  playSpeechSample('en');
                }}
                className="flex items-center gap-2 px-5 py-3.5 rounded-xl bg-[#13263A] text-[#00D4FF] border border-[#20384D] hover:border-[#00D4FF]/50 font-bold text-sm transition-all cursor-pointer"
              >
                <Mic className="w-4 h-4 text-[#00D4FF]" />
                <span>Talk to Safety Advisor</span>
              </button>
            </div>

            {/* Compact Simulation Telemetry Strip */}
            <div className="bg-[#0D1B2A] border border-[#20384D] rounded-xl p-3.5 space-y-2 font-mono shadow-lg">
              <div className="flex items-center justify-between text-[11px] border-b border-[#20384D]/70 pb-2">
                <div className="flex items-center gap-2 text-[#18C7A0] font-semibold">
                  <div className="w-2 h-2 rounded-full bg-[#18C7A0] animate-pulse" />
                  <span>SYSTEM ONLINE // SIMULATION FEED ACTIVE</span>
                </div>
                <span className="text-[#8FA8B8] text-[10px]">DIURNAL STEP: 24H</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[10px]">
                <div className="bg-[#13263A] p-2 rounded border border-[#20384D]">
                  <span className="text-[#8FA8B8] block text-[9px] uppercase">Active Sim Fleet</span>
                  <span className="text-[#EAF4F8] font-bold text-xs">104 Vessels</span>
                </div>
                <div className="bg-[#13263A] p-2 rounded border border-[#20384D]">
                  <span className="text-[#8FA8B8] block text-[9px] uppercase">Enforced Boundaries</span>
                  <span className="text-[#00D4FF] font-bold text-xs">12 Zones</span>
                </div>
                <div className="bg-[#13263A] p-2 rounded border border-[#20384D]">
                  <span className="text-[#8FA8B8] block text-[9px] uppercase">Grid Resolution</span>
                  <span className="text-[#18C7A0] font-bold text-xs">0.4° Mesh</span>
                </div>
              </div>
            </div>

          </div>

          {/* Right Column: Custom 3D Tactical Globe */}
          <div className="lg:col-span-6">
            <TacticalGlobe 
              onLaunchConsole={() => handleLaunch('map')}
            />
          </div>

        </div>
      </section>

      {/* 3. Live System Telemetry Bulletin / Feed */}
      <section id="telemetry" className="border-y border-[#20384D] bg-[#0D1B2A] py-2.5 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 flex items-center gap-4">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#13263A] border border-[#20384D] text-[10px] font-mono font-bold text-[#00D4FF] whitespace-nowrap">
            <Activity className="w-3 h-3 animate-spin" />
            <span>LIVE BULLETIN</span>
          </div>

          <div className="overflow-x-auto no-scrollbar flex items-center gap-6 text-[11px] font-mono text-[#8FA8B8] whitespace-nowrap">
            {TELEMETRY_FEED.map((feed, idx) => (
              <div key={idx} className="flex items-center gap-2 flex-shrink-0">
                <span 
                  className="px-1.5 py-0.2 rounded text-[9px] font-bold"
                  style={{ color: feed.color, backgroundColor: `${feed.color}15`, border: `1px solid ${feed.color}40` }}
                >
                  [{feed.type}]
                </span>
                <span className="text-[#EAF4F8]">{feed.text}</span>
                {idx < TELEMETRY_FEED.length - 1 && <span className="text-[#20384D]">///</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. "How Navik Thinks" Step-by-Step User Journey */}
      <section id="how-it-thinks" className="py-20 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="space-y-4 mb-12">
          <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
            <Sparkles className="w-4 h-4" />
            <span>OPERATIONAL WORKFLOW</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
            HOW NAVIK THINKS: STEP-BY-STEP USER JOURNEY
          </h2>
          <p className="text-sm text-[#8FA8B8] max-w-2xl">
            From natural language vocal query in coastal fishing dialects to deterministic safety advisories quoting official regulations.
          </p>
        </div>

        {/* Horizontal Step Stepper */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-8">
          {USER_JOURNEY_STEPS.map((item, idx) => (
            <button
              key={item.step}
              onClick={() => setSelectedJourneyStep(idx)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                selectedJourneyStep === idx
                  ? 'bg-[#13263A] border-[#00D4FF] shadow-[0_0_15px_rgba(0,212,255,0.15)]'
                  : 'bg-[#0D1B2A] border-[#20384D] hover:border-[#8FA8B8]/40'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-[10px] font-mono font-bold ${
                  selectedJourneyStep === idx ? 'text-[#00D4FF]' : 'text-[#8FA8B8]'
                }`}>
                  {item.step} // {item.phase}
                </span>
                {selectedJourneyStep === idx && (
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00D4FF]" />
                )}
              </div>
              <div className="text-xs font-semibold text-[#EAF4F8] truncate">
                {item.title}
              </div>
            </button>
          ))}
        </div>

        {/* Active Journey Detail Card */}
        <div className="bg-[#13263A] border border-[#20384D] rounded-2xl p-6 lg:p-8 space-y-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#20384D] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-bold">
                  PHASE {activeJourney.step}: {activeJourney.phase}
                </span>
                <span className="text-xs font-mono text-[#8FA8B8]">
                  ACTOR: {activeJourney.actor}
                </span>
              </div>
              <h3 className="text-xl font-bold text-[#EAF4F8] mt-2">
                {activeJourney.title}
              </h3>
            </div>

            <div className="flex items-center gap-2">
              <button
                disabled={selectedJourneyStep === 0}
                onClick={() => setSelectedJourneyStep(p => Math.max(0, p - 1))}
                className="px-3 py-1.5 rounded bg-[#0D1B2A] border border-[#20384D] text-xs font-mono text-[#8FA8B8] hover:text-[#EAF4F8] disabled:opacity-30 cursor-pointer"
              >
                PREV STEP
              </button>
              <button
                disabled={selectedJourneyStep === USER_JOURNEY_STEPS.length - 1}
                onClick={() => setSelectedJourneyStep(p => Math.min(USER_JOURNEY_STEPS.length - 1, p + 1))}
                className="px-3 py-1.5 rounded bg-[#00D4FF] text-[#07111F] font-bold text-xs font-mono hover:bg-[#00D4FF]/90 disabled:opacity-30 cursor-pointer"
              >
                NEXT STEP ➔
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 space-y-4">
              <div className="bg-[#07111F] border border-[#20384D] rounded-xl p-4">
                <span className="text-[10px] font-mono uppercase text-[#8FA8B8] block mb-1">Operational Dialogue / Input</span>
                <p className="text-sm font-mono text-[#00D4FF] italic">
                  {activeJourney.quote}
                </p>
              </div>

              <p className="text-sm text-[#8FA8B8] leading-relaxed">
                {activeJourney.detail}
              </p>
            </div>

            <div className="lg:col-span-5 bg-[#07111F] border border-[#20384D] rounded-xl p-4 font-mono space-y-2">
              <span className="text-[10px] uppercase text-[#8FA8B8] block">
                {activeJourney.outputLabel}
              </span>
              <pre className="text-xs text-[#18C7A0] whitespace-pre-wrap bg-[#0D1B2A] p-3 rounded border border-[#20384D] overflow-x-auto">
                {activeJourney.outputVal}
              </pre>
            </div>
          </div>
        </div>

      </section>

      {/* 5. 9 Specialized Collaborative AI Agents Ecosystem */}
      <section id="agents-ecosystem" className="py-20 px-4 lg:px-8 bg-[#0D1B2A]/50 border-y border-[#20384D]">
        <div className="max-w-7xl mx-auto space-y-12">
          
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
              <Cpu className="w-4 h-4" />
              <span>COLLABORATIVE MULTI-AGENT ARCHITECTURE</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
              9 SPECIALIZED COLLABORATIVE AI AGENTS
            </h2>
            <p className="text-sm text-[#8FA8B8] max-w-2xl">
              An asynchronous event-driven stateful orchestrator executing task decomposition, scientific slicing, ML risk classification, and grounded RAG compliance.
            </p>
          </div>

          {/* Collaborative Orchestrator DAG Topology Flow Graph */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-2xl p-6 lg:p-8 space-y-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#20384D] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#00D4FF] animate-ping" />
                <span className="text-xs font-mono font-bold tracking-wider text-[#EAF4F8] uppercase">
                  EVENT-DRIVEN MULTI-AGENT ORCHESTRATION DAG
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#18C7A0] bg-[#07111F] px-2.5 py-1 rounded border border-[#20384D]">
                ● 7 CONCURRENT PIPELINES ACTIVE // SIMULATION FEED
              </span>
            </div>

            {/* Visual Graph Nodes & Directed Flow */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
              {/* Node 1: User Interaction Agent */}
              <div 
                onClick={() => setSelectedAgentIndex(0)}
                className={`lg:col-span-3 p-4 rounded-xl border transition-all cursor-pointer space-y-2 ${
                  selectedAgentIndex === 0 
                    ? 'bg-[#0D1B2A] border-[#00D4FF] shadow-[0_0_15px_rgba(0,212,255,0.2)] scale-[1.02]' 
                    : 'bg-[#07111F] border-[#20384D] hover:border-[#8FA8B8]/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-[#00D4FF] font-bold">NODE 01 // FRONT-END</span>
                  <Mic className="w-3.5 h-3.5 text-[#00D4FF]" />
                </div>
                <div className="text-xs font-bold text-[#EAF4F8]">User Interaction Agent</div>
                <div className="text-[10px] font-mono text-[#8FA8B8]">Voice (EN/HI/MR) & Web Speech API</div>
              </div>

              {/* Directed Arrow 1 */}
              <div className="hidden lg:flex lg:col-span-1 justify-center">
                <div className="flex items-center text-[#00D4FF] animate-pulse">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>

              {/* Node 2: Planner Agent (Hub) */}
              <div 
                onClick={() => setSelectedAgentIndex(1)}
                className={`lg:col-span-4 p-4 rounded-xl border transition-all cursor-pointer space-y-2 ${
                  selectedAgentIndex === 1 
                    ? 'bg-[#0D1B2A] border-[#00D4FF] shadow-[0_0_20px_rgba(0,212,255,0.25)] scale-[1.02]' 
                    : 'bg-[#07111F] border-[#00D4FF]/40 hover:border-[#00D4FF]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-[#00D4FF] font-bold">NODE 02 // ORCHESTRATOR HUB</span>
                  <Cpu className="w-4 h-4 text-[#00D4FF] animate-spin" />
                </div>
                <div className="text-xs font-bold text-[#EAF4F8]">Planner Agent (Stateful DAG)</div>
                <div className="text-[10px] font-mono text-[#18C7A0]">Task Decomposition & Failsafe Guard</div>
              </div>

              {/* Directed Arrow 2 */}
              <div className="hidden lg:flex lg:col-span-1 justify-center">
                <div className="flex items-center text-[#00D4FF] animate-pulse">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>

              {/* Node Target: Synthesized Output */}
              <div className="lg:col-span-3 p-4 rounded-xl bg-[#07111F] border border-[#18C7A0]/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-[#18C7A0] font-bold">SYNTHESIZED TARGET</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#18C7A0]" />
                </div>
                <div className="text-xs font-bold text-[#EAF4F8]">Safe Geofenced Advisory</div>
                <div className="text-[10px] font-mono text-[#8FA8B8]">GeoJSON Map + Spoken Readback</div>
              </div>
            </div>

            {/* Parallel Sub-Agent Fast Selector Strip */}
            <div className="bg-[#07111F] p-4 rounded-xl border border-[#20384D] space-y-2">
              <div className="text-[10px] font-mono text-[#8FA8B8] uppercase">
                Parallel Distributed Execution Pipelines (Click to inspect):
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
                {AGENT_SPECIFICATIONS.slice(2).map((agent, i) => {
                  const actualIdx = i + 2;
                  const isSelected = selectedAgentIndex === actualIdx;
                  const Icon = agent.icon;
                  return (
                    <button
                      key={agent.id}
                      onClick={() => setSelectedAgentIndex(actualIdx)}
                      className={`p-2 rounded-lg border text-left transition-all cursor-pointer ${
                        isSelected 
                          ? 'bg-[#13263A] border-[#00D4FF] shadow-sm scale-[1.02]' 
                          : 'bg-[#0D1B2A] border-[#20384D] hover:border-[#8FA8B8]/40'
                      }`}
                    >
                      <div className="flex items-center gap-1 mb-1">
                        <Icon className="w-3 h-3" style={{ color: agent.color }} />
                        <span className="text-[9px] font-mono font-bold" style={{ color: agent.color }}>
                          {agent.num}
                        </span>
                      </div>
                      <div className="text-[10px] font-bold text-[#EAF4F8] truncate">
                        {agent.name.replace(' Agent', '')}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Connected Agent Flow Visualization Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {AGENT_SPECIFICATIONS.map((agent, idx) => {
              const Icon = agent.icon;
              const isSelected = selectedAgentIndex === idx;

              return (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgentIndex(idx)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-3 ${
                    isSelected
                      ? 'bg-[#13263A] border-[#00D4FF] shadow-[0_0_20px_rgba(0,212,255,0.15)] scale-[1.01]'
                      : 'bg-[#0D1B2A] border-[#20384D] hover:border-[#8FA8B8]/40'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div 
                        className="p-2 rounded-lg"
                        style={{ backgroundColor: `${agent.color}15`, border: `1px solid ${agent.color}40` }}
                      >
                        <Icon className="w-4 h-4" style={{ color: agent.color }} />
                      </div>
                      <div>
                        <span className="text-[10px] font-mono text-[#8FA8B8] block">
                          AGENT {agent.num}
                        </span>
                        <h4 className="text-sm font-bold text-[#EAF4F8]">
                          {agent.name}
                        </h4>
                      </div>
                    </div>

                    <span 
                      className="text-[9px] font-mono px-2 py-0.5 rounded font-bold"
                      style={{ color: agent.color, backgroundColor: `${agent.color}10`, border: `1px solid ${agent.color}30` }}
                    >
                      {agent.status}
                    </span>
                  </div>

                  <p className="text-xs text-[#8FA8B8] line-clamp-2">
                    {agent.description}
                  </p>

                  <div className="text-[10px] font-mono text-[#8FA8B8] pt-1 border-t border-[#20384D]/60 flex items-center justify-between">
                    <span className="text-[#EAF4F8] font-semibold">{agent.role}</span>
                    <span className="text-[#00D4FF]">DETAILS ➔</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Deep Agent Specification Inspector Panel */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-2xl p-6 lg:p-8 space-y-6 shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#20384D] pb-4">
              <div className="flex items-center gap-3">
                <div 
                  className="p-3 rounded-xl"
                  style={{ backgroundColor: `${activeAgent.color}15`, border: `1px solid ${activeAgent.color}40` }}
                >
                  <activeAgent.icon className="w-6 h-6" style={{ color: activeAgent.color }} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-[#00D4FF]">
                      AGENT {activeAgent.num} // SPECIFICATION
                    </span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#07111F] text-[#18C7A0] border border-[#20384D]">
                      {activeAgent.status}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[#EAF4F8]">
                    {activeAgent.name} — <span className="text-sm font-normal text-[#8FA8B8]">{activeAgent.role}</span>
                  </h3>
                </div>
              </div>

              <div className="text-xs font-mono text-[#8FA8B8] bg-[#07111F] px-3 py-1.5 rounded border border-[#20384D]">
                ENGINE: <span className="text-[#EAF4F8] font-bold">{activeAgent.tech}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              <div className="bg-[#07111F] p-4 rounded-xl border border-[#20384D] space-y-2">
                <span className="text-[10px] text-[#8FA8B8] uppercase block">Data Inputs & Triggers</span>
                <p className="text-[#EAF4F8]">{activeAgent.inputs}</p>
              </div>

              <div className="bg-[#07111F] p-4 rounded-xl border border-[#20384D] space-y-2">
                <span className="text-[10px] text-[#8FA8B8] uppercase block">Synthesized Outputs & Actions</span>
                <p className="text-[#18C7A0]">{activeAgent.outputs}</p>
              </div>
            </div>

            <p className="text-sm text-[#8FA8B8]">
              {activeAgent.description}
            </p>
          </div>

        </div>
      </section>

      {/* 6. Core Capabilities Matrix */}
      <section id="capabilities" className="py-20 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="space-y-4 mb-12">
          <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
            <Layers className="w-4 h-4" />
            <span>CORE FEATURE MATRIX</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
            BUILT FOR NAVAL OPERATIONS & FISHERIES RESILIENCE
          </h2>
          <p className="text-sm text-[#8FA8B8] max-w-2xl">
            Strictly adhering to SIH26176 evaluation rubrics with zero black-box logic, predictive geofencing, and offline-first failsafes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CAPABILITY_CARDS.map((card, idx) => {
            const Icon = card.icon;
            return (
              <div 
                key={idx}
                className="bg-[#13263A] border border-[#20384D] rounded-2xl p-6 space-y-4 hover:border-[#00D4FF]/40 transition-all shadow-lg flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div 
                      className="p-2.5 rounded-xl"
                      style={{ backgroundColor: `${card.color}15`, border: `1px solid ${card.color}40` }}
                    >
                      <Icon className="w-5 h-5" style={{ color: card.color }} />
                    </div>
                    <span 
                      className="text-[9px] font-mono px-2 py-0.5 rounded font-bold"
                      style={{ color: card.color, backgroundColor: `${card.color}10`, border: `1px solid ${card.color}30` }}
                    >
                      {card.category}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-[#EAF4F8]">
                    {card.title}
                  </h3>

                  <p className="text-xs text-[#8FA8B8] leading-relaxed">
                    {card.summary}
                  </p>
                </div>

                <div className="space-y-2 pt-4 border-t border-[#20384D]/70 text-[11px] font-mono text-[#8FA8B8]">
                  {card.points.map((pt, pIdx) => (
                    <div key={pIdx} className="flex items-start gap-2">
                      <span className="text-[#00D4FF]">▹</span>
                      <span className="text-[#EAF4F8]">{pt}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 7. Progressive Disclosure FAQ Panel */}
      <section id="faq" className="py-20 px-4 lg:px-8 bg-[#0D1B2A]/60 border-t border-[#20384D]">
        <div className="max-w-4xl mx-auto space-y-10">
          
          <div className="space-y-4 text-center">
            <div className="inline-flex items-center gap-2 text-xs font-mono text-[#00D4FF] bg-[#13263A] px-3 py-1 rounded-md border border-[#20384D]">
              <HelpCircle className="w-4 h-4" />
              <span>JUDGING & TECHNICAL AUDIT</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
              PROGRESSIVE DISCLOSURE FAQ
            </h2>
            <p className="text-sm text-[#8FA8B8] max-w-xl mx-auto">
              Simple explanations for high-level evaluation, with collapsible technical details for architecture and algorithmic deep-dives.
            </p>
          </div>

          <div className="space-y-4">
            {FAQ_ITEMS.map((faq) => {
              const isExpanded = expandedFaqId === faq.id;
              const isTechOpen = showTechnicalDetails[faq.id];

              return (
                <div 
                  key={faq.id}
                  className="bg-[#13263A] border border-[#20384D] rounded-xl overflow-hidden transition-all shadow-md"
                >
                  <button
                    onClick={() => setExpandedFaqId(isExpanded ? null : faq.id)}
                    className="w-full p-5 text-left flex items-center justify-between gap-4 hover:bg-[#13263A]/80 transition-colors cursor-pointer"
                  >
                    <span className="text-sm sm:text-base font-bold text-[#EAF4F8]">
                      {faq.question}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-[#00D4FF] flex-shrink-0" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[#8FA8B8] flex-shrink-0" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="px-5 pb-5 space-y-4 border-t border-[#20384D]/70 pt-4">
                      {/* Simple Answer */}
                      <p className="text-sm text-[#8FA8B8] leading-relaxed">
                        {faq.simple}
                      </p>

                      {/* Technical Deep Dive Button & Collapsible Block */}
                      <div className="pt-2">
                        <button
                          onClick={() => toggleTechnical(faq.id)}
                          className="flex items-center gap-2 text-xs font-mono font-bold text-[#00D4FF] hover:text-[#00D4FF]/80 transition-colors cursor-pointer"
                        >
                          <Code2 className="w-3.5 h-3.5" />
                          <span>{isTechOpen ? 'HIDE TECHNICAL DETAILS [-]' : 'VIEW TECHNICAL DETAILS [+]'}</span>
                        </button>

                        {isTechOpen && (
                          <div className="mt-3 bg-[#07111F] border border-[#20384D] rounded-lg p-4 font-mono text-xs">
                            <pre className="text-[#18C7A0] whitespace-pre-wrap font-mono text-[11px] leading-relaxed">
                              {faq.technical}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

        </div>
      </section>

      {/* 8. Tactical Call-to-Action Console Banner */}
      <section className="py-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="relative bg-gradient-to-r from-[#0D1B2A] via-[#13263A] to-[#0D1B2A] border border-[#20384D] rounded-3xl p-8 lg:p-12 overflow-hidden shadow-2xl">
          {/* Neon Top Accent Line */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00D4FF] to-transparent" />

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-8 space-y-3">
              <span className="text-xs font-mono text-[#00D4FF] font-bold uppercase tracking-wider">
                SIH26176 READY-TO-EVALUATE DEMO
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
                EXPERIENCE THE LIVE OPERATIONS CONSOLE
              </h2>
              <p className="text-sm text-[#8FA8B8] max-w-xl">
                Explore the interactive MapLibre spatial canvas with dynamic SVAS BSI grids, Recharts 24-hour diurnal timelines, and real-time beam vulnerability sliders.
              </p>
            </div>

            <div className="lg:col-span-4 flex flex-col sm:flex-row lg:flex-col gap-3 justify-end">
              <button
                onClick={() => handleLaunch('map')}
                className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-[#00D4FF] text-[#07111F] font-extrabold text-sm hover:shadow-[0_0_30px_rgba(0,212,255,0.4)] transition-all cursor-pointer"
              >
                <Compass className="w-4 h-4" />
                <span>Launch Operations Console</span>
              </button>

              <button
                onClick={() => {
                  setIsAdvisorModalOpen(true);
                  playSpeechSample('en');
                }}
                className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#07111F] text-[#00D4FF] border border-[#20384D] hover:border-[#00D4FF]/40 font-bold text-xs transition-all cursor-pointer"
              >
                <Mic className="w-4 h-4" />
                <span>Talk to Safety Advisor</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 9. Tactical Footer HUD */}
      <footer className="bg-[#0D1B2A] border-t border-[#20384D] pt-12 pb-8 px-4 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-8">
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            
            {/* Brand & Mission */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#00D4FF]" />
                <span className="font-extrabold text-sm tracking-widest text-[#EAF4F8] font-mono">
                  NAVIK PLATFORM
                </span>
              </div>
              <p className="text-xs text-[#8FA8B8] leading-relaxed">
                Intelligent Marine Decision-Support Platform developed for Smart India Hackathon (SIH26176). Autonomous multi-agent coordination with deterministic safety floors.
              </p>
            </div>

            {/* Console Navigation */}
            <div className="space-y-2 font-mono text-xs">
              <span className="text-[11px] text-[#EAF4F8] font-bold uppercase tracking-wider block mb-2">
                Console Navigation
              </span>
              <ul className="space-y-1.5 text-[#8FA8B8]">
                <li><button onClick={() => handleLaunch('map')} className="hover:text-[#00D4FF] transition-colors cursor-pointer">➔ Interactive Map Canvas</button></li>
                <li><button onClick={() => { setIsAdvisorModalOpen(true); playSpeechSample('en'); }} className="hover:text-[#00D4FF] transition-colors cursor-pointer">➔ AI Safety Advisor</button></li>
                <li><a href="#how-it-thinks" className="hover:text-[#00D4FF] transition-colors">➔ 5-Step Workflow</a></li>
                <li><a href="#agents-ecosystem" className="hover:text-[#00D4FF] transition-colors">➔ 9-Agent Graph</a></li>
              </ul>
            </div>

            {/* Scientific Data Provenance */}
            <div className="space-y-2 font-mono text-xs">
              <span className="text-[11px] text-[#EAF4F8] font-bold uppercase tracking-wider block mb-2">
                Scientific Provenance
              </span>
              <ul className="space-y-1.5 text-[#8FA8B8]">
                <li><span className="text-[#18C7A0]">●</span> INCOIS THREDDS OPeNDAP</li>
                <li><span className="text-[#18C7A0]">●</span> ISRO MOSDAC Telemetry</li>
                <li><span className="text-[#18C7A0]">●</span> IMD RSMC Cyclone Alerts</li>
                <li><span className="text-[#18C7A0]">●</span> GEBCO Bathymetry Contours</li>
              </ul>
            </div>

            {/* Tactical Monospace Terminal HUD */}
            <div className="bg-[#07111F] border border-[#20384D] rounded-xl p-3.5 font-mono text-[11px] space-y-1.5 text-[#8FA8B8]">
              <div className="flex items-center justify-between text-[#00D4FF] border-b border-[#20384D] pb-1 font-bold text-[10px]">
                <span>TACTICAL HUD</span>
                <span className="text-[#18C7A0]">● LIVE</span>
              </div>
              <div className="text-[10px] space-y-1">
                <div>SYSTEM: <span className="text-[#EAF4F8]">ONLINE // SIM ACTIVE</span></div>
                <div>DATABASE: <span className="text-[#EAF4F8]">NEON-POSTGIS (pgvector)</span></div>
                <div>GEOFENCE: <span className="text-[#EAF4F8]">5.0 KM SECTOR BUFFER</span></div>
                <div>FALLBACK: <span className="text-[#18C7A0]">SQLite 3.42 READY</span></div>
                <div>BUILD: <span className="text-[#00D4FF]">v1.0.0-PROD (SIH26176)</span></div>
              </div>
            </div>

          </div>

          {/* Bottom Copyright & Disclaimer */}
          <div className="pt-6 border-t border-[#20384D]/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[#8FA8B8]">
            <div>
              © 2026 Navik Marine Intelligence. Developed for Smart India Hackathon.
            </div>
            <div className="flex items-center gap-4 text-[11px]">
              <span className="text-[#18C7A0]">SECURITY: ZERO-EXTERNAL SPEECH LEAK</span>
              <span className="text-[#00D4FF]">PALETTE: FROZEN NAVIK</span>
            </div>
          </div>

        </div>
      </footer>

      {/* 10. Multilingual Voice Safety Advisor Preview Modal */}
      {isAdvisorModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="relative w-full max-w-2xl bg-[#13263A] border border-[#20384D] rounded-3xl overflow-hidden shadow-2xl space-y-6 p-6 lg:p-8 animate-in fade-in zoom-in duration-200">
            {/* Top Glowing Border */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00D4FF] to-transparent" />

            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#20384D] pb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-2xl bg-[#00D4FF]/10 border border-[#00D4FF]/30 text-[#00D4FF]">
                  <Mic className="w-6 h-6 animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-[#00D4FF] uppercase">
                      AGENT 01 // WEB SPEECH API
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#07111F] text-[#18C7A0] border border-[#20384D]">
                      ZERO-COST CLIENT SYNTHESIS
                    </span>
                  </div>
                  <h3 className="text-lg sm:text-xl font-bold text-[#EAF4F8]">
                    AI Safety Advisor Vocal Readback
                  </h3>
                </div>
              </div>

              <button
                onClick={closeAdvisorModal}
                className="p-1.5 rounded-lg text-[#8FA8B8] hover:text-[#EAF4F8] hover:bg-[#07111F] transition-colors cursor-pointer"
                title="Close Advisor Modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Language Selection Tabs */}
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-[#8FA8B8] uppercase block">Select Coastal Fishing Dialect:</span>
              <div className="grid grid-cols-3 gap-2">
                {Object.keys(ADVISORY_SAMPLES).map((key) => (
                  <button
                    key={key}
                    onClick={() => playSpeechSample(key)}
                    className={`py-2.5 px-3 rounded-xl border text-xs font-bold font-mono transition-all cursor-pointer ${
                      advisorLang === key
                        ? 'bg-[#00D4FF] text-[#07111F] border-[#00D4FF] shadow-md'
                        : 'bg-[#07111F] text-[#8FA8B8] border-[#20384D] hover:border-[#00D4FF]/40'
                    }`}
                  >
                    {ADVISORY_SAMPLES[key].langName}
                  </button>
                ))}
              </div>
            </div>

            {/* Captured Natural Language Query */}
            <div className="bg-[#07111F] border border-[#20384D] rounded-xl p-4 space-y-1 font-mono">
              <span className="text-[10px] text-[#8FA8B8] uppercase block">Captured Vocal Query</span>
              <p className="text-xs sm:text-sm text-[#00D4FF] italic">
                {ADVISORY_SAMPLES[advisorLang].query}
              </p>
            </div>

            {/* Synthesized Voice Advisory & Audio Controls */}
            <div className="bg-[#0D1B2A] border border-[#20384D] rounded-2xl p-4 sm:p-5 space-y-4 shadow-inner">
              <div className="flex items-center justify-between border-b border-[#20384D]/70 pb-3">
                <div className="flex items-center gap-2">
                  <Volume2 className={`w-4 h-4 ${isSpeaking ? 'text-[#18C7A0] animate-bounce' : 'text-[#8FA8B8]'}`} />
                  <span className="text-xs font-mono font-bold text-[#EAF4F8]">
                    {isSpeaking ? 'VOICE SYNTHESIS ACTIVE...' : 'PHONETIC REGIONAL SYNTHESIS'}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {isSpeaking ? (
                    <button
                      onClick={stopSpeech}
                      className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#FF5C5C]/20 border border-[#FF5C5C]/50 text-[#FF5C5C] text-xs font-mono font-bold hover:bg-[#FF5C5C]/30 cursor-pointer"
                    >
                      <Square className="w-3 h-3" />
                      <span>STOP</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => playSpeechSample(advisorLang)}
                      className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#18C7A0]/20 border border-[#18C7A0]/50 text-[#18C7A0] text-xs font-mono font-bold hover:bg-[#18C7A0]/30 cursor-pointer"
                    >
                      <Play className="w-3 h-3" />
                      <span>PLAY VOCAL READOUT</span>
                    </button>
                  )}
                </div>
              </div>

              <p className="text-xs sm:text-sm text-[#EAF4F8] leading-relaxed">
                "{ADVISORY_SAMPLES[advisorLang].spoken}"
              </p>

              <div className="pt-2 border-t border-[#20384D]/60 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono">
                <span className="text-[#18C7A0] font-bold">
                  {ADVISORY_SAMPLES[advisorLang].display}
                </span>
                <span className="text-[#8FA8B8] bg-[#07111F] px-2 py-0.5 rounded border border-[#20384D]">
                  CITATION: {ADVISORY_SAMPLES[advisorLang].citation}
                </span>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
              <span className="text-[10px] font-mono text-[#8FA8B8]">
                Native Web Speech API (No external server data leakage)
              </span>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <button
                  onClick={closeAdvisorModal}
                  className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-[#07111F] text-[#8FA8B8] hover:text-[#EAF4F8] border border-[#20384D] text-xs font-mono font-bold cursor-pointer"
                >
                  Close
                </button>
                <button
                  onClick={() => handleLaunch('advisor')}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#00D4FF] text-[#07111F] text-xs font-mono font-extrabold hover:bg-[#00D4FF]/90 cursor-pointer"
                >
                  <span>Open in Console</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
