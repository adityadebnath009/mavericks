# Mavericks Project Rules: Multi-Agent Architecture & Grading Constraints

All development, modifications, and feature additions in this repository must strictly adhere to the following multi-agent system specifications, product feature sets, and grading guidelines for the Smart India Hackathon (SIH26176).

---

## 1. The 9 Specialized AI Agents

We decompose the platform into **9 specialized, collaborative AI agents** that run concurrently to resolve complex user queries:

1.  **User Interaction Agent (Multi-turn, Localization & Voice):**
    *   **Role:** The front-end liaison. Natively integrates the browser's **Web Speech API** for zero-cost multilingual voice inputs and read-aloud spoken advice (English, Hindi, Marathi).
2.  **Planner Agent (Task Decomposition & Failsafe Resilience):**
    *   **Role:** The coordinator and error handler. Decomposes queries and delegates sub-tasks.
    *   **Failsafe Rule:** If the PostgreSQL/PostGIS database is down or remote weather APIs time out, the Planner must automatically switch downstream execution to a **local file fallback** (JSON/SQLite cached scenarios) to prevent app crashes.
3.  **Marine Data Discovery Agent (Honest Provider Interface):**
    *   **Role:** The data retriever. Wraps live endpoints behind an interface mapping keyless Open-Meteo services in development, enabling production-grade ISRO MOSDAC or INCOIS telemetry feeds to swap in without breaking downstream logic.
4.  **Weather Intelligence Agent:**
    *   **Role:** Meteorological analyzer. Identifies depressions, wind speed, lightning, and visibility hazards.
5.  **Ocean Analytics Agent:**
    *   **Role:** Oceanographic analyst. Identifies Potential Fishing Zones (PFZs) using SST and Chlorophyll-a gradients, as well as wave heights and swell periods.
6.  **Geospatial Reasoning Agent (PostGIS Spatial Engine):**
    *   **Role:** Spatial calculator. Performs spatial database lookups (`ST_Contains`, `ST_Distance`) against `india_eez` and `marine_protected_areas` tables to geofence vessels near borders and ecological sanctuaries.
7.  **Risk Assessment Agent (XGBoost + Deterministic Floors):**
    *   **Role:** Safety classifier. Uses a trained **XGBoost Classifier** on weather/wave metrics.
    *   **Failsafe Rule:** ML risk output must be capped by **deterministic safety floors** (e.g. Cyclone warnings force 92, IMD warnings force 70, waves >= 4m force 85) to ensure safety calculations are mathematically secure.
8.  **Visualization Agent:**
    *   **Role:** UI builder. Generates interactive maps, geofenced alerts, and charts.
9.  **Reporting Agent (Grounded RAG):**
    *   **Role:** Compliance compiler. Performs semantic searches against regulatory manuals (FAO guides, Coast Guard codes) using pgvector and generates plain-language, cited rationales.

---

## 2. Core Feature Matrix & Dataset Mappings

Every feature developed in this repository must map to the following architectural and dataset guidelines:

| Feature Name | Target Specification | Dataset/Resource Path | Stack |
| :--- | :--- | :--- | :--- |
| **1. Marine Risk Predictor** | Localized safety risks (LOW to EXTREME) + confidence. | `data/processed/marine_risk_processed.csv` | XGBoost Classifier, Scikit-learn, Pandas |
| **2. Safe-Route Optimization** | Safest routes generated *around* PostGIS restricted zones / MPAs using A*. | `data/processed/` and PostGIS boundary layers | NetworkX (A* pathfinding with node risk costs) |
| **3. Geofencing & Borders** | Live warnings for EEZ/IMBL proximity and restricted MPAs. | `india_eez` and `marine_protected_areas` database tables | GeoPandas, SQLAlchemy, PostGIS (Neon DB) |
| **4. Grounded Safety Advisor** | RAG bot quoting official clauses and PDFs with pgvector. | `data/regulatory/fao_*.pdf`, `data/regulatory/marine_safety_corpus.json` | pgvector vector database, BGE-M3 Embeddings, Gemini API |
| **5. Multilingual Voice Outreach** | Multilingual responses and browser-based voice processing. | Client-side localization dictionaries | Web Speech API, React state |
| **6. Offline-First Resilience** | Seamless fallback to local JSON/SQLite cache if server drops. | Static JSON forecasts, SQLite geometry backups | SQLite, FastAPI middleware |

---

## 3. Core Grading Standards & Competitive Edge Rules

*   **Explainability (No Black Box):** Every safety assessment must justify its rating (LOW, MODERATE, HIGH, EXTREME) by citing specific parameters (e.g. wave height) and mapping them to official guidelines (e.g. CMFRI/INCOIS advisories).
*   **Predictive Geofencing:** Continuous checking of vessel coordinates must flag approaches to restricted zones or maritime boundaries *before* crossing, based on vector drift.
*   **Single-Process Local Deployment:** The React frontend assets must be served statically from FastAPI so the entire app runs on a single port (`127.0.0.1:8000`) with no extra configurations.
*   **Unified Database (PostGIS + pgvector):** All spatial and semantic/vector data must reside in the same PostgreSQL database to allow hybrid spatial-vector queries in one database round-trip.
*   **Split Temporal Validation:** ML models must be trained using temporal splitting (e.g. training on older years, validation on future holdout years) to prevent data leakage and ensure real-world generalization.
