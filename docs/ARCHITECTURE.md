# System Architecture

This document defines the technical architecture of our intelligent marine safety and decision-support platform (ORCA/Mavericks).

---

## 1. Architecture Diagram

```mermaid
graph TD
    %% Data Ingestion Layer
    subgraph Layer 1: Data Ingestion & Normalization
        INCOIS[INCOIS SVAS API / GeoJSON] --> Ingest[Ingestion Pipeline]
        OM[Open-Meteo API / Waves & Winds] --> Ingest
        Bound[PostGIS shapefiles / EEZ & MPAs] --> Ingest
    end

    %% Storage Layer
    subgraph Layer 2: Database Storage (PostgreSQL / Neon)
        Ingest --> DB[(PostgreSQL + PostGIS)]
        Local[(Offline-First SQLite Cache)]
    end

    %% Logic Services
    subgraph Layer 3: Scientific & Processing Engines
        DB --> BSI[1. Scientific BSI Engine]
        DB --> Vessel[2. Vessel Vulnerability Engine]
        DB --> Geofence[3. PostGIS Geofencing Engine]
        DB --> Route[4. Risk-Aware A* Routing Service]
    end

    %% API Controller Layer
    subgraph Layer 4: API & Decision Layer
        BSI --> API[FastAPI REST Controllers]
        Vessel --> API
        Geofence --> API
        Route --> API
        API --> Agent[LLM Explainability Agent]
    end

    %% Presentation Layer
    subgraph Layer 5: User Interface (React)
        API --> Map[MapLibre GL Map Overlays]
        API --> Timeline[Forecast Timeline & Charts]
        API --> Voice[Web Speech Voice Synthesis]
        Agent --> Text[Human-Readable cited Alerts]
    end

    %% Feedback Loop
    subgraph Layer 6: Feedback Loop
        Feedback[User Sea-State Reports] --> DB
    end
```

---

## 2. Layer-by-Layer Specifications

### Layer 1: Ingestion & Normalization
*   Fetches real-time wave heights, swell directions, wave periods, and currents from keyless Open-Meteo endpoints.
*   Pulls district-level advisory zones and BSI coordinates from INCOIS geo-services.
*   Caches raw data into a localized format to normalize coordinates (WGS84 EPSG:4326) and timestamps (ISO 8601).

### Layer 2: Unified Database Storage
*   Stores geopolitical boundaries (`india_eez` table) and ecological zones (`marine_protected_areas` table).
*   Enables spatial distance calculation using PostGIS indices.
*   **Offline Fallback:** If PostgreSQL is unreachable or weather service connection timeouts occur, requests are routed to a local SQLite schema/cached JSON files.

### Layer 3: Scientific & Processing Engines
1.  **Scientific BSI Engine:** Calculates the Steepness Index, Crossing Sea Index, and Rapid Development Index using SWAN/WW3 wave inputs, returning a weighted BSI value (0-7).
2.  **Vessel Vulnerability Engine:** Accepts a vessel profile (beam width) and evaluates the critical beam formula ($4 \times H_s$) to calculate personalized stability alerts.
3.  **PostGIS Geofencing Engine:** Checks proximity to restricted zones and computes geodesic distance to the closest border edge.
4.  **Risk-Aware Route Optimizer:** Constructs a coordinate grid in NetworkX, assigning travel weights based on geographic distance, weather parameters, and restricted polygon walls, searching for the safest path using $A^*$.

### Layer 4: Decision & Agent Layer
*   Exposes endpoints to retrieve real-time safety scores, calculated routes, and boundary status.
*   Provides structured metrics to the Agentic Layer.
*   **Gemini Agent:** Translates the structured metrics into contextual warnings without inventing forecasts (e.g. converting BSI=5 and Critical Beam violation into a cited plain-language safety alert).

### Layer 5: User Interface (React)
*   **MapLibre GL JS:** Renders spatial risk heatmaps, vessel coordinates, geofences, and calculated routes.
*   **Speech System:** Utilizes browser-native Web Speech API for voice inputs (hearing search queries) and voice outputs (reading alerts aloud in Hindi, Marathi, and English).
