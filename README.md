# Mavericks: Navik Marine Portal

Mavericks is an intelligent spatial decision support platform for Potential Fishing Zones (PFZs), weather safety routing, and predictive border/sanctuary geofencing in the North Indian Ocean. By coordinating a **9-agent specialized AI architecture**, Mavericks integrates real-time oceanographic observations, spatial queries, and machine learning risk predictors into an explainable, localized, and offline-resilient system.

---

## 1. Architectural Vision

Mavericks is designed to bridge the gap between complex meteorological data and practical, safety-critical maritime guidance. The platform coordinates distributed data discovery, spatial boundaries checks, and machine learning risk modeling behind a unified, single-port deployment model.

```
+-----------------------------------------------------------------------------------+
|                                 Client React UI                                   |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTPS JSON/REST / WMS Layer Requests
                                         v
+-----------------------------------------------------------------------------------+
|                                 FastAPI Backend                                   |
+-----------------------------------------------------------------------------------+
       |                      |                      |                     |
       | Spatial Queries      | Semantic Queries     | Incident Prediction | Ingestion
       v                      v                      v                     v
+------------+        +------------+        +---------------+      +----------------+
|  PostGIS   |        |  pgvector  |        |    XGBoost    |      |   INCOIS /     |
| (Database) |        | (Database) |        | (Risk Model)  |      | Open-Meteo API |
+------------+        +------------+        +---------------+      +----------------+
       |                      |                      |                     |
       +----------+-----------+                      v                     |
                  |                     +--------------------+             |
                  v                     | Deterministic      |             |
       +----------------------+         | Safety Floors      |             |
       |   Neon PostgreSQL    |         +--------------------+             |
       | (Central Datastore)  |                      |                     |
       +----------------------+                      v                     v
                  |                            [ Risk Score ]        [ TTL Cache ]
                  v (Failover)                                             |
       +----------------------+                                            |
       |    Local SQLite      |<-------------------------------------------+
       | (& Fallback GeoJSON) |
       +----------------------+
```

### Core Architectural Pillars
- **Explainability (No Black Box):** Every risk output justifies its hazard category (LOW, MODERATE, HIGH, EXTREME) by citing specific parameters (e.g. wave heights) and linking them to official marine guidelines.
- **Unified Spatial-Vector DB:** PostGIS and pgvector reside in a single Neon PostgreSQL instance, enabling hybrid spatial boundaries checking and regulatory RAG queries to run in a single database round-trip.
- **Single-Process Local Deployment:** Built React frontend static assets are served directly via FastAPI endpoints, allowing the entire application to run seamlessly on a single port (`127.0.0.1:8000`).
- **Offline-First Resilience:** A dedicated SQLite and GeoJSON fallback pipeline monitors backend connectivity, automatically serving cached data if PostgreSQL or remote weather APIs drop.

---

## 2. Core Feature Matrix & Dataset Mappings

Every core feature maps to specific data sources and implementation layers:

| Feature Name | Target Specification | Dataset / Resource Path | Technical Stack |
| :--- | :--- | :--- | :--- |
| **1. Marine Risk Predictor** | Localized safety risks (LOW to EXTREME) + confidence. | `data/processed/marine_risk_processed.csv` | XGBoost Classifier, Scikit-learn, Pandas |
| **2. Safe-Route Optimization** | Safest paths around PostGIS restricted zones / MPAs using Dijkstra/A*. | `data/processed/` & PostGIS boundaries | NetworkX (A* pathfinding with node risk costs) |
| **3. Geofencing & Borders** | Live warnings for EEZ/IMBL proximity and restricted MPAs. | `india_eez` and `marine_protected_areas` tables | GeoPandas, SQLAlchemy, PostGIS (Neon DB) |
| **4. Grounded Safety Advisor** | RAG bot quoting official clauses and PDFs with pgvector. | `data/regulatory/fao_*.pdf`, `marine_safety_corpus.json` | pgvector, BGE-M3 Embeddings, Gemini API |
| **5. Multilingual Voice Outreach** | Multilingual responses and browser-based voice processing. | Client-side localization dictionaries | Web Speech API, React state |
| **6. Offline-First Resilience** | Seamless fallback to local JSON/SQLite cache if server drops. | Static JSON forecasts, SQLite geometry backups | SQLite, FastAPI middleware |

---

## 3. The 9 Specialized AI Agents

The platform decomposes complex maritime inquiries into **9 collaborative, concurrent AI agents**:

```
                  +--------------------------------+
                  |     User Interaction Agent     |<--- Voice / Text
                  +--------------------------------+
                                  |
                                  | Decoded User Intent
                                  v
                  +--------------------------------+
                  |         Planner Agent          |
                  +--------------------------------+
                                  |
                                 Decomposes and Orchestrates Tasks
                             +----+----+
                             |    |    |
                             v    v    v
                      [ Agents 3 - 7: Processing ]
                             |    |    |
                             +----+----+
                                  |
                                  v
                  +--------------------------------+
                  |      Visualization Agent       | ---> Map overlays (MapLibre)
                  +--------------------------------+
                                  |
                                  v
                  +--------------------------------+
                  |        Reporting Agent         | ---> Citations & RAG (pgvector)
                  +--------------------------------+
```

1. **User Interaction Agent (Multi-turn, Localization & Voice):** Natively integrates the browser's **Web Speech API** for zero-cost multilingual voice inputs and read-aloud spoken advice (supporting English, Hindi, and Marathi).
2. **Planner Agent (Task Decomposition & Failsafe Resilience):** The coordinator and error handler. Decomposes queries and delegates sub-tasks.
   * *Failsafe Rule:* If PostgreSQL/PostGIS is down or remote weather APIs time out, it automatically shifts downstream execution to the local file fallback (SQLite/JSON cached scenarios) to prevent app crashes.
3. **Marine Data Discovery Agent (Honest Provider Interface):** Wraps live endpoints behind an interface mapping keyless Open-Meteo services in development, enabling production-grade ISRO MOSDAC or INCOIS telemetry feeds to swap in without breaking downstream logic.
4. **Weather Intelligence Agent:** Meteorological analyzer. Identifies depressions, wind speed, lightning, and visibility hazards.
5. **Ocean Analytics Agent:** Oceanographic analyst. Identifies Potential Fishing Zones (PFZs) using SST and Chlorophyll-a gradients, as well as wave heights and swell periods.
6. **Geospatial Reasoning Agent (PostGIS Spatial Engine):** Performs spatial database lookups (`ST_Contains`, `ST_Distance`) against `india_eez` and `marine_protected_areas` tables to geofence vessels near borders and sanctuaries.
7. **Risk Assessment Agent (XGBoost + Deterministic Floors):** Computes machine learning safety confidence scores.
   * *Failsafe Rule:* ML risk output is strictly capped by **deterministic safety floors** (e.g. Cyclone warnings force 92, IMD warnings force 70, waves $\ge 4.0$m force 85) to ensure safety calculations are mathematically secure.
8. **Visualization Agent:** UI asset builder. Translates coordinates, safe routes, and warning boundaries into MapLibre GL GeoJSON FeatureCollections, mapping risk levels to semantic colors (`green`, `yellow`, `orange`, `red`).
9. **Reporting Agent (Grounded RAG):** Compliance compiler. Performs semantic searches against regulatory manuals (FAO guides, Coast Guard codes) using pgvector and generates plain-language, cited rationales.

---

## 4. Engineering & Algorithmic Engines

### A. Current-Aware Vector Routing Logic
Our route optimizer accounts for the direction and velocity of surface currents by projecting them onto the boat's heading.

When analyzing path segments from grid node $u(\phi_1, \lambda_1)$ to node $v(\phi_2, \lambda_2)$:
1. **Calculate Boat Bearing ($\theta_{\text{boat}}$):**
   $$\theta_{\text{boat}} = \text{atan2}\left(\sin(\Delta\lambda)\cos(\phi_2), \cos(\phi_1)\sin(\phi_2) - \sin(\phi_1)\cos(\phi_2)\cos(\Delta\lambda)\right)$$
2. **Current Vector Difference ($\Delta\theta$):**
   $$\Delta\theta = \theta_{\text{current}} - \theta_{\text{boat}}$$
3. **Calculate Parallel Speed ($V_{\text{current,parallel}}$):**
   $$V_{\text{current,parallel}} = V_{\text{current}} \times \cos(\Delta\theta)$$
   *(where $V_{\text{current}}$ is converted from m/s to km/h).*
4. **Effective Boat Speed ($V_{\text{effective}}$):**
   $$V_{\text{effective}} = \max\left(2.0, \min\left(30.0, V_{\text{boat}} + V_{\text{current,parallel}} - \text{Wave Drag}\right)\right)$$
5. **Transit Time Cost ($T$):**
   $$T = \frac{\text{Distance}}{V_{\text{effective}}}$$

The engine uses a **Dual Dijkstra Pathfinding** framework:
- **Safest & Current-Optimized Path:** Computes edge weights based on travel times derived from $V_{\text{effective}}$, BSI capsize penalties, and warning buffers. Favorable currents minimize segment weights.
- **Shortest Direct Path:** Runs pathfinding based solely on distance, avoiding restricted zones, and evaluates actual transit risk post-routing.

### B. Machine Learning Risk & Safety Floors
Safety scoring balances machine learning adaptability with deterministic compliance rules:
- **Model:** An XGBoost Classifier trained on waves, wind, currents, bathymetry, and distance to shore. Split temporal validation (training on older years, validation on future holdout years) is used to prevent data leakage.
- **Deterministic Override Safety Floors:** Regardless of ML confidence, hard ceilings are applied when safety thresholds are breached:
  - Cyclone warnings $\rightarrow$ Risk Score = 92 (Extreme)
  - Gale force wind / IMD warning $\rightarrow$ Risk Score = 70 (High)
  - Wave heights $\ge 4.0$m $\rightarrow$ Risk Score = 85 (Extreme)

### C. Grounded Safety Advisor (pgvector RAG)
The RAG pipeline extracts semantic chunks from official maritime safety manuals and encodes them using BGE-M3 embeddings.
- **Embedding Database:** Single database instance with pgvector.
- **Distance Metric:** Cosine similarity.
- **Explainability:** Generates cited regulatory excerpts alongside every route risk evaluation, guaranteeing clear compliance justifications for fishing vessels.
