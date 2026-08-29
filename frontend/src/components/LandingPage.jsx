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
  CheckCircle2, 
  ArrowRight, 
  ChevronDown, 
  ChevronUp, 
  Navigation, 
  Activity, 
  Sparkles, 
  Server, 
  Code2, 
  HelpCircle,
  X,
  Play,
  Square,
  Network,
  Zap,
  Info
} from 'lucide-react';
import TacticalGlobe from './TacticalGlobe';
import SpotlightCard from './SpotlightCard';

// 9 Specialized AI Agents Data & Technical Specifications
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

// Section 2: How Navik Thinks: Step-by-Step User Journey
const USER_JOURNEY_STEPS = [
  {
    step: '01',
    phase: 'ASK',
    title: 'Natural Language Query',
    tag: 'VOICE OR TEXT',
    quote: '"Find me a safe route from Kochi to Lakshadweep leaving tomorrow morning."',
    actor: '01. User Interaction Agent',
    detail: 'Captured natively via browser Web Speech API in English, Hindi (हिन्दी), or Marathi (मराठी) with zero external speech API cost.',
    outputLabel: 'Decoded Intent Payload',
    outputVal: '{ origin: "Kochi Port", destination: "Lakshadweep (Kavaratti)", depart_time: "2026-08-29T06:00:00Z", vessel_beam_m: 3.5 }'
  },
  {
    step: '02',
    phase: 'UNDERSTAND',
    title: 'Intent Parsing & Task Decomposition',
    tag: 'TASK GRAPH DISPATCH',
    quote: 'Decomposing query parameters, temporal departure window, and vessel stability limits.',
    actor: '02. Planner Agent (Coordinator)',
    detail: 'Extracts spatial coordinates, departure windows, and vessel constraints. Decomposes task into concurrent sub-agent jobs with failsafe local fallback readiness.',
    outputLabel: 'Execution DAG Envelope',
    outputVal: 'Dispatched 7 Concurrent Pipelines: [Marine Data Discovery, Weather Hazard, Ocean Analytics, PostGIS Geofence, XGBoost Risk]'
  },
  {
    step: '03',
    phase: 'ANALYZE',
    title: 'Multi-Source Scientific Slicing',
    tag: 'SCIENTIFIC DATA FUSION',
    quote: 'Interpolating WaveWatch III rasters, ocean current velocities, and PostGIS boundary layers.',
    actor: '03-06. Discovery, Weather & Geospatial Agents',
    detail: 'Fetches 24-hour diurnal timelines for wave height (Hs), peak period (T02), surface currents, and performs PostGIS ST_Contains checks against EEZ & MPAs.',
    outputLabel: 'Interpolated 0.4° Mesh',
    outputVal: 'Wave Height: 1.2m, Swell Period: 6.5s, Surface Current: 0.35 m/s SE, EEZ Distance: 116.9 km (CLEAR)'
  },
  {
    step: '04',
    phase: 'OPTIMIZE',
    title: 'Current-Aware Vector Routing',
    tag: 'DIJKSTRA PATHFINDING',
    quote: 'Dijkstra engine calculating current drift projection (Vc · cos Δθ) bypassing restricted MPAs.',
    actor: '06-08. Geospatial, Risk & Visualization Agents',
    detail: 'Calculates optimal waypoint transitions across a 0.4° graph. Steers clear of restricted eco-zones while riding favorable surface current vectors for fuel efficiency.',
    outputLabel: 'Optimal Vector Arc',
    outputVal: 'Route Distance: 215 NM, Projected Fuel Efficiency: +18%, Wave Steepness: 0.012 (Safe Margin), Avoided MPAs: Gulf of Mannar'
  },
  {
    step: '05',
    phase: 'ADVISE',
    title: 'Explainable Grounded Advisory',
    tag: 'GROUNDED RAG & VOICE',
    quote: '"Safe to venture into sea. Departure recommended at 06:00 UTC. CMFRI Guideline Clause 4.2 cited."',
    actor: '08-09. Reporting & Visualization Agents',
    detail: 'Renders the safe route on the MapLibre tactical canvas, charts 24h diurnal trends, and vocalizes the safety verdict quoting official maritime safety codes via pgvector.',
    outputLabel: 'Verified Advisory Verdict',
    outputVal: 'RATING: SAFE (BSI 1/7) // DEPARTURE WINDOW: 06:00 UTC (+2H OPTIMAL) // CITATION: FAO Small Craft Code §4.2 • CMFRI Advisory'
  }
];

// Section 4: Core Capabilities Matrix (6 Compact Cards)
const CAPABILITY_CARDS = [
  {
    icon: Shield,
    title: 'Marine Risk Predictor',
    category: 'ML + SAFETY FLOORS',
    color: '#FFB547',
    summary: 'Machine learning safety classifier combined with non-negotiable deterministic safety floor overrides.',
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
    summary: 'Zero-cost client-side speech recognition and vocal read-back in coastal fishing languages.',
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

// Section 5: Live System Telemetry Bulletins
const TELEMETRY_FEED = [
  { type: 'SYS', color: '#18C7A0', text: 'INCOIS GeoServer & OPeNDAP proxy ONLINE // 0.4° resolution diurnal grid synchronized.' },
  { type: 'GEO', color: '#00D4FF', text: 'Vessel Sagar Kanya updated coordinates (17.43°N, 84.70°E). EEZ buffer clear: 116.9 km.' },
  { type: 'WARN', color: '#FFB547', text: 'Significant wave height warning (Hs >= 3.5m) in Gujarat Coastline. Small craft advisory.' },
  { type: 'RISK', color: '#FF5C5C', text: 'Deterministic safety floor active in Sector-4 due to IMD Squally Weather bulletin.' },
  { type: 'RAG', color: '#00D4FF', text: 'pgvector semantic index primed: 1,420 regulatory safety clauses embedded.' },
  { type: 'FLEET', color: '#18C7A0', text: 'Active Simulation Fleet: 104 vessels operating within monitored EEZ sectors.' }
];

// Section 6: Progressive Disclosure FAQ Items
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

// Multilingual Advisory Samples for Web Speech Testing
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
  // Stepper & Popover States
  const [selectedJourneyStep, setSelectedJourneyStep] = useState(0);
  const [activeAgentId, setActiveAgentId] = useState(null);
  const [hoveredAgentId, setHoveredAgentId] = useState(null);
  const [expandedFaqId, setExpandedFaqId] = useState('faq-1');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState({ 'faq-1': true });
  const [isAdvisorModalOpen, setIsAdvisorModalOpen] = useState(false);
  const [advisorLang, setAdvisorLang] = useState('en');
  const [isSpeaking, setIsSpeaking] = useState(false);

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

  // Inspect active agent in Node Graph (either hovered or clicked)
  const currentAgentInspectionId = activeAgentId || hoveredAgentId;
  const inspectedAgent = AGENT_SPECIFICATIONS.find(a => a.id === currentAgentInspectionId);

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
          <a href="#agents-graph" className="hover:text-[#00D4FF] transition-colors">02 // 9 AGENTS</a>
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

      {/* 2. Hero Section (Split View - Concise & Impactful) */}
      <section id="hero" className="relative pt-8 pb-14 px-4 lg:px-8 max-w-7xl mx-auto">
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

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={() => handleLaunch('map')}
                className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-[#00D4FF] text-[#07111F] font-extrabold text-sm shadow-[0_0_15px_rgba(0,212,255,0.3)] hover:shadow-[0_0_25px_rgba(0,212,255,0.6)] transition-shadow duration-300 cursor-pointer"
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
                  <span>SIMULATION ACTIVE</span>
                </div>
                <span className="text-[#8FA8B8] text-[10px]">FORECAST STEP: 24H</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[10px]">
                <div className="bg-[#13263A] p-2 rounded border border-[#20384D]">
                  <span className="text-[#8FA8B8] block text-[9px] uppercase">Sim Fleet</span>
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

      {/* 3. "How Navik Thinks" Step-by-Step User Journey (Positioned Immediately Below Hero) */}
      <section id="how-it-thinks" className="py-16 px-4 lg:px-8 max-w-7xl mx-auto border-t border-[#20384D]/70">
        <div className="space-y-3 mb-8">
          <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
            <Sparkles className="w-4 h-4" />
            <span>OPERATIONAL USER JOURNEY</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
            HOW NAVIK THINKS: STEP-BY-STEP FLOW
          </h2>
          <p className="text-sm text-[#8FA8B8] max-w-2xl">
            From natural language voice query in coastal fishing dialects to deterministic, mathematically verified maritime safety advisories.
          </p>
        </div>

        {/* 5-Step Horizontal Interactive Flowchart Stepper */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 mb-6">
          {USER_JOURNEY_STEPS.map((item, idx) => {
            const isSelected = selectedJourneyStep === idx;
            return (
              <button
                key={item.step}
                onClick={() => setSelectedJourneyStep(idx)}
                className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#13263A] border-[#00D4FF] shadow-[0_0_15px_rgba(0,212,255,0.18)] scale-[1.01]'
                    : 'bg-[#0D1B2A] border-[#20384D] hover:border-[#8FA8B8]/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-mono font-bold ${
                    isSelected ? 'text-[#00D4FF]' : 'text-[#8FA8B8]'
                  }`}>
                    {item.step} // {item.phase}
                  </span>
                  {isSelected && (
                    <div className="w-2 h-2 rounded-full bg-[#00D4FF] animate-pulse" />
                  )}
                </div>
                <div className="text-xs font-bold text-[#EAF4F8] truncate">
                  {item.title}
                </div>
              </button>
            );
          })}
        </div>

        {/* Active Journey Detail Card */}
        <div className="bg-[#13263A] border border-[#20384D] rounded-2xl p-6 lg:p-8 space-y-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#20384D] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/30 font-bold">
                  PHASE {activeJourney.step}: {activeJourney.phase}
                </span>
                <span className="text-xs font-mono text-[#8FA8B8]">
                  PRIMARY ACTOR: <span className="text-[#EAF4F8] font-semibold">{activeJourney.actor}</span>
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
              <pre className="text-xs text-[#18C7A0] whitespace-pre-wrap bg-[#0D1B2A] p-3 rounded border border-[#20384D] overflow-x-auto leading-relaxed">
                {activeJourney.outputVal}
              </pre>
            </div>
          </div>
        </div>

      </section>

      {/* 4. 9-Agent Collaborative Node Graph (Clean Interactive Node Graph with Hover/Click Overlays) */}
      <section id="agents-graph" className="py-16 px-4 lg:px-8 bg-[#0D1B2A]/50 border-y border-[#20384D]">
        <div className="max-w-7xl mx-auto space-y-8">
          
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
              <Network className="w-4 h-4" />
              <span>COLLABORATIVE MULTI-AGENT ARCHITECTURE</span>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
                  9-AGENT COLLABORATIVE NODE GRAPH
                </h2>
                <p className="text-sm text-[#8FA8B8] max-w-2xl mt-1">
                  Hover or click any agent node in the topology graph to inspect its role, data feeds, and execution triggers. Saturated Cyan pulses animate along active connection links.
                </p>
              </div>
              
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#13263A] border border-[#20384D] text-xs font-mono text-[#18C7A0]">
                <Zap className="w-3.5 h-3.5 text-[#00D4FF] animate-pulse" />
                <span>STATEFUL ASYNC DAG // 7 CONCURRENT WORKERS</span>
              </div>
            </div>
          </div>

          {/* Interactive Topology Graph Container */}
          <div className="bg-[#13263A] border border-[#20384D] rounded-2xl p-5 lg:p-7 shadow-2xl relative overflow-hidden">
            
            {/* Ambient Background Grid Texture */}
            <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#00D4FF_1px,transparent_1px)] [background-size:16px_16px]" />

            {/* Desktop & Tablet Node Graph Topology Flow */}
            <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              
              {/* Column 1: Stage 1 - User Interaction Agent (Node 01) */}
              <div className="lg:col-span-3 space-y-3 relative">
                <div className="text-[10px] font-mono uppercase text-[#00D4FF] font-bold tracking-wider flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-pulse" />
                  <span>STAGE 1: USER INPUT</span>
                </div>

                <div
                  onMouseEnter={() => setHoveredAgentId('agent-01')}
                  onMouseLeave={() => setHoveredAgentId(null)}
                  onClick={() => setActiveAgentId(activeAgentId === 'agent-01' ? null : 'agent-01')}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2 relative group ${
                    currentAgentInspectionId === 'agent-01'
                      ? 'bg-[#0D1B2A] border-[#00D4FF] shadow-[0_0_20px_rgba(0,212,255,0.25)] scale-[1.02]'
                      : 'bg-[#07111F] border-[#20384D] hover:border-[#00D4FF]/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-[#00D4FF] font-bold">NODE 01</span>
                    <div className="p-1.5 rounded-lg bg-[#00D4FF]/10 text-[#00D4FF]">
                      <Mic className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="text-sm font-bold text-[#EAF4F8]">User Interaction Agent</div>
                  <div className="text-[11px] font-mono text-[#8FA8B8]">Voice (EN/HI/MR) & Web Speech</div>
                  
                  <div className="text-[9px] font-mono text-[#18C7A0] pt-1 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#18C7A0]" />
                    <span>ZERO-COST SPEECH RECOGNITION</span>
                  </div>
                </div>

                {/* Animated Connection Link: Stage 1 ➔ Stage 2 */}
                <div className="flex items-center justify-between text-[10px] font-mono text-[#8FA8B8] pt-1 bg-[#07111F]/60 px-2.5 py-1.5 rounded-lg border border-[#20384D]/60">
                  <span className="text-[#8FA8B8]">Decoded Intent</span>
                  <div className="flex items-center gap-1.5">
                    <svg className="w-10 h-3 text-[#00D4FF]" viewBox="0 0 40 12" fill="none">
                      <line x1="0" y1="6" x2="32" y2="6" stroke="#00D4FF" strokeWidth="1.5" strokeDasharray="4 4" className="animate-flow" />
                      <polygon points="32,3 39,6 32,9" fill="#00D4FF" />
                    </svg>
                    <span className="text-[#00D4FF] font-bold">➔</span>
                  </div>
                </div>
              </div>

              {/* Column 2: Stage 2 - Planner Coordinator (Node 02) */}
              <div className="lg:col-span-3 space-y-3 relative">
                <div className="text-[10px] font-mono uppercase text-[#00D4FF] font-bold tracking-wider flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-ping" />
                  <span>STAGE 2: ORCHESTRATOR HUB</span>
                </div>

                <div
                  onMouseEnter={() => setHoveredAgentId('agent-02')}
                  onMouseLeave={() => setHoveredAgentId(null)}
                  onClick={() => setActiveAgentId(activeAgentId === 'agent-02' ? null : 'agent-02')}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2 relative group ${
                    currentAgentInspectionId === 'agent-02'
                      ? 'bg-[#0D1B2A] border-[#00D4FF] shadow-[0_0_25px_rgba(0,212,255,0.3)] scale-[1.02]'
                      : 'bg-[#07111F] border-[#00D4FF]/40 hover:border-[#00D4FF]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-[#00D4FF] font-bold">NODE 02 // HUB</span>
                    <div className="p-1.5 rounded-lg bg-[#00D4FF]/10 text-[#00D4FF]">
                      <Cpu className="w-4 h-4 animate-spin" />
                    </div>
                  </div>
                  <div className="text-sm font-bold text-[#EAF4F8]">Planner Agent (DAG Hub)</div>
                  <div className="text-[11px] font-mono text-[#18C7A0]">Task Graph & Failsafe Guard</div>
                  
                  <div className="text-[9px] font-mono text-[#8FA8B8] pt-1 flex items-center gap-1">
                    <span className="text-[#00D4FF]">⇋</span>
                    <span>AUTO LOCAL SQLITE FALLBACK</span>
                  </div>
                </div>

                {/* Animated Connection Link: Stage 2 ➔ Stage 3 */}
                <div className="flex items-center justify-between text-[10px] font-mono text-[#8FA8B8] pt-1 bg-[#07111F]/60 px-2.5 py-1.5 rounded-lg border border-[#20384D]/60">
                  <span className="text-[#18C7A0] font-semibold">7 Parallel Workers</span>
                  <div className="flex items-center gap-1.5">
                    <svg className="w-10 h-3 text-[#00D4FF]" viewBox="0 0 40 12" fill="none">
                      <line x1="0" y1="6" x2="32" y2="6" stroke="#00D4FF" strokeWidth="1.5" strokeDasharray="4 4" className="animate-flow" />
                      <polygon points="32,3 39,6 32,9" fill="#00D4FF" />
                    </svg>
                    <span className="text-[#00D4FF] font-bold">➔</span>
                  </div>
                </div>
              </div>

              {/* Column 3: Stage 3 - Parallel Sub-Agent Nodes (Nodes 03 to 09) */}
              <div className="lg:col-span-4 space-y-2 relative">
                <div className="text-[10px] font-mono uppercase text-[#00D4FF] font-bold tracking-wider flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#18C7A0] animate-pulse" />
                    <span>STAGE 3: PARALLEL DISPATCH (03-09)</span>
                  </span>
                  <span className="text-[9px] text-[#8FA8B8]">CLICK / HOVER</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2 max-h-[360px] overflow-y-auto pr-1 no-scrollbar">
                  {AGENT_SPECIFICATIONS.slice(2).map((agent) => {
                    const Icon = agent.icon;
                    const isSelected = currentAgentInspectionId === agent.id;

                    return (
                      <div
                        key={agent.id}
                        onMouseEnter={() => setHoveredAgentId(agent.id)}
                        onMouseLeave={() => setHoveredAgentId(null)}
                        onClick={() => setActiveAgentId(activeAgentId === agent.id ? null : agent.id)}
                        className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between gap-2 ${
                          isSelected
                            ? 'bg-[#0D1B2A] border-[#00D4FF] shadow-[0_0_15px_rgba(0,212,255,0.2)] scale-[1.01]'
                            : 'bg-[#07111F] border-[#20384D] hover:border-[#8FA8B8]/40'
                        }`}
                      >
                        <div className="flex items-center gap-2.5 truncate">
                          <div 
                            className="p-1.5 rounded"
                            style={{ backgroundColor: `${agent.color}15`, border: `1px solid ${agent.color}40` }}
                          >
                            <Icon className="w-3.5 h-3.5" style={{ color: agent.color }} />
                          </div>
                          <div className="truncate text-left">
                            <div className="text-xs font-bold text-[#EAF4F8] truncate">
                              <span className="font-mono text-[10px] mr-1" style={{ color: agent.color }}>
                                {agent.num}.
                              </span>
                              {agent.name.replace(' Agent', '')}
                            </div>
                            <div className="text-[9px] font-mono text-[#8FA8B8] truncate">
                              {agent.role.split('&')[0]}
                            </div>
                          </div>
                        </div>

                        <span 
                          className="text-[8px] font-mono px-1.5 py-0.5 rounded font-bold whitespace-nowrap flex-shrink-0"
                          style={{ color: agent.color, backgroundColor: `${agent.color}10`, border: `1px solid ${agent.color}30` }}
                        >
                          {agent.status.split(' ')[0]}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Column 4: Stage 4 - Target Output ([ SAFE ROUTE ]) */}
              <div className="lg:col-span-2 space-y-3 relative">
                <div className="text-[10px] font-mono uppercase text-[#18C7A0] font-bold tracking-wider flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#18C7A0] animate-pulse" />
                  <span>TARGET OUTPUT</span>
                </div>

                <div 
                  onClick={() => handleLaunch('map')}
                  className="p-4 rounded-xl bg-[#07111F] border border-[#18C7A0]/60 space-y-2 hover:border-[#18C7A0] hover:shadow-[0_0_20px_rgba(24,199,160,0.2)] transition-all cursor-pointer text-left"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono text-[#18C7A0] font-bold">SYNTHESIZED</span>
                    <CheckCircle2 className="w-4 h-4 text-[#18C7A0]" />
                  </div>
                  <div className="text-xs font-bold text-[#EAF4F8]">Safe Route Advisory</div>
                  <div className="text-[10px] font-mono text-[#8FA8B8]">GeoJSON Overlay + Spoken Verdict</div>
                  
                  <div className="pt-2 border-t border-[#20384D] flex items-center justify-between text-[9px] font-mono text-[#00D4FF] font-bold">
                    <span>EXPLORE ➔</span>
                  </div>
                </div>

                {/* Synthesis Link Badge */}
                <div className="flex items-center justify-center gap-1.5 text-[9px] font-mono text-[#18C7A0] bg-[#07111F]/60 px-2 py-1 rounded border border-[#20384D]/60">
                  <Zap className="w-3 h-3 text-[#00D4FF] animate-pulse" />
                  <span>SYNTHESIZED DAG</span>
                </div>
              </div>

            </div>

            {/* Dynamic Node Overlay / Popover Inspector Card (Shown on Hover / Click) */}
            {inspectedAgent ? (
              <div className="mt-6 pt-5 border-t border-[#20384D] animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="bg-[#13263A] border border-[#00D4FF]/40 rounded-xl p-5 space-y-4 shadow-xl relative">
                  
                  {/* Close button if pinned */}
                  {activeAgentId && (
                    <button
                      onClick={() => setActiveAgentId(null)}
                      className="absolute top-3 right-3 p-1 rounded-lg text-[#8FA8B8] hover:text-[#EAF4F8] hover:bg-[#07111F] transition-colors cursor-pointer"
                      title="Close Inspector"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}

                  <div className="flex flex-wrap items-center justify-between gap-3 pr-8">
                    <div className="flex items-center gap-3">
                      <div 
                        className="p-2.5 rounded-xl"
                        style={{ backgroundColor: `${inspectedAgent.color}15`, border: `1px solid ${inspectedAgent.color}40` }}
                      >
                        <inspectedAgent.icon className="w-5 h-5" style={{ color: inspectedAgent.color }} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-[#00D4FF]">
                            AGENT {inspectedAgent.num} // SPECIFICATION
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#07111F] text-[#18C7A0] border border-[#20384D]">
                            {inspectedAgent.status}
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-[#EAF4F8]">
                          {inspectedAgent.name} — <span className="text-xs font-normal text-[#8FA8B8]">{inspectedAgent.role}</span>
                        </h4>
                      </div>
                    </div>

                    <div className="text-xs font-mono text-[#8FA8B8] bg-[#07111F] px-3 py-1 rounded border border-[#20384D]">
                      ENGINE: <span className="text-[#EAF4F8] font-bold">{inspectedAgent.tech}</span>
                    </div>
                  </div>

                  <p className="text-xs text-[#EAF4F8] leading-relaxed">
                    {inspectedAgent.description}
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs pt-1">
                    <div className="bg-[#07111F] p-3 rounded-lg border border-[#20384D] space-y-1">
                      <span className="text-[9px] text-[#8FA8B8] uppercase block">Data Inputs & Triggers</span>
                      <p className="text-[#EAF4F8] text-[11px]">{inspectedAgent.inputs}</p>
                    </div>

                    <div className="bg-[#07111F] p-3 rounded-lg border border-[#20384D] space-y-1">
                      <span className="text-[9px] text-[#8FA8B8] uppercase block">Synthesized Outputs & Actions</span>
                      <p className="text-[#18C7A0] text-[11px]">{inspectedAgent.outputs}</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-4 pt-3 border-t border-[#20384D]/50 flex items-center justify-between text-xs font-mono text-[#8FA8B8]">
                <div className="flex items-center gap-2">
                  <Info className="w-3.5 h-3.5 text-[#00D4FF]" />
                  <span>Tip: Click or hover on any agent node above to inspect its live data contracts and algorithms.</span>
                </div>
                <span className="text-[10px] text-[#00D4FF] hidden sm:inline-block">EVENT-DRIVEN ARCHITECTURE</span>
              </div>
            )}

          </div>

        </div>
      </section>

      {/* 5. Core Capabilities Matrix (6 Compact Cards) */}
      <section id="capabilities" className="py-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="space-y-3 mb-10">
          <div className="flex items-center gap-2 text-xs font-mono text-[#00D4FF]">
            <Layers className="w-4 h-4" />
            <span>CORE FEATURE MATRIX</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
            BUILT FOR NAVAL OPERATIONS & FISHERIES RESILIENCE
          </h2>
          <p className="text-sm text-[#8FA8B8] max-w-2xl">
            Strictly adhering to SIH26176 evaluation rubrics with zero black-box logic, predictive geofencing, and offline-first resilience.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CAPABILITY_CARDS.map((card, idx) => {
            const Icon = card.icon;
            return (
              <SpotlightCard 
                key={idx}
                className="p-6 space-y-4 shadow-lg flex flex-col justify-between h-full hover:border-[#00D4FF]/40 transition-colors"
                spotlightColor="rgba(0, 212, 255, 0.10)"
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
              </SpotlightCard>
            );
          })}
        </div>
      </section>

      {/* 6. Live System Telemetry Scrolling Marquee Ticker */}
      <section id="telemetry" className="border-y border-[#20384D] bg-[#0D1B2A] py-2.5 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 flex items-center gap-4">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#13263A] border border-[#20384D] text-[10px] font-mono font-bold text-[#00D4FF] whitespace-nowrap z-10 flex-shrink-0">
            <Activity className="w-3 h-3 animate-spin" />
            <span>LIVE BULLETIN</span>
          </div>

          {/* Continuous CSS Marquee Container */}
          <div className="overflow-hidden flex-1 relative no-scrollbar">
            <div className="animate-marquee flex items-center gap-8 text-[11px] font-mono text-[#8FA8B8] whitespace-nowrap">
              {/* Duplicate the items to allow seamless infinite looping */}
              {[...TELEMETRY_FEED, ...TELEMETRY_FEED].map((feed, idx) => (
                <div key={idx} className="flex items-center gap-2 flex-shrink-0">
                  <span 
                    className="px-1.5 py-0.2 rounded text-[9px] font-bold"
                    style={{ color: feed.color, backgroundColor: `${feed.color}15`, border: `1px solid ${feed.color}40` }}
                  >
                    [{feed.type}]
                  </span>
                  <span className="text-[#EAF4F8]">{feed.text}</span>
                  <span className="text-[#20384D] ml-4">///</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 7. Progressive Disclosure FAQ Panel */}
      <section id="faq" className="py-16 px-4 lg:px-8 bg-[#0D1B2A]/60 border-b border-[#20384D]">
        <div className="max-w-4xl mx-auto space-y-8">
          
          <div className="space-y-3 text-center">
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

      {/* 8. Launch Console CTA (Closing Block) */}
      <section id="launch-console" className="py-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="relative bg-gradient-to-r from-[#0D1B2A] via-[#13263A] to-[#0D1B2A] border border-[#20384D] rounded-3xl p-8 lg:p-12 overflow-hidden shadow-2xl">
          {/* Neon Top Accent Line */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#00D4FF] to-transparent" />

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-8 space-y-3">
              <span className="text-xs font-mono text-[#00D4FF] font-bold uppercase tracking-wider">
                READY FOR DEPLOYMENT // SIH26176
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#EAF4F8]">
                LAUNCH OPERATIONS CONSOLE
              </h2>
              <p className="text-sm text-[#8FA8B8] max-w-xl">
                Explore the interactive MapLibre spatial canvas with dynamic SVAS BSI grids, Recharts 24-hour diurnal timelines, and real-time beam vulnerability calculations.
              </p>
            </div>

            <div className="lg:col-span-4 flex flex-col sm:flex-row lg:flex-col gap-3 justify-end">
              <button
                onClick={() => handleLaunch('map')}
                className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-[#00D4FF] text-[#07111F] font-extrabold text-sm shadow-[0_0_15px_rgba(0,212,255,0.3)] hover:shadow-[0_0_25px_rgba(0,212,255,0.6)] transition-shadow duration-300 cursor-pointer"
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
                <li><a href="#how-it-thinks" className="hover:text-[#00D4FF] transition-colors">➔ 5-Step User Journey</a></li>
                <li><a href="#agents-graph" className="hover:text-[#00D4FF] transition-colors">➔ 9-Agent Node Graph</a></li>
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
                <div>SYSTEM STATUS: <span className="text-[#EAF4F8]">ONLINE // SIMULATION ACTIVE</span></div>
                <div>DATABASE PORT: <span className="text-[#EAF4F8]">NEON-POSTGIS (pgvector)</span></div>
                <div>SECTOR BUFFER: <span className="text-[#EAF4F8]">5.0 KM</span></div>
                <div>VERSION STATUS: <span className="text-[#00D4FF]">v1.0.0-PROD</span></div>
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
                Native Web Speech API (Zero cloud server data leakage)
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
