# Product Differentiation Matrix

This document defines how our intelligent marine safety and decision-support platform (ORCA/Mavericks) improves upon the scientific and functional baseline established by the INCOIS Small Vessel Advisory Services (SVAS).

| Feature / Dimension | Existing INCOIS SVAS | Our Intelligent Platform | SIH Competitive Advantage |
| :--- | :--- | :--- | :--- |
| **Vessel Risk Model** | 3 static categories based on beam width (<4m, <6m, <7m). | **Continuous Vessel Profile:** Tracks specific beam width, length, draft, engine capacity, and fishing gear. | Personalized safety limits tailored to the exact stability dynamics of the fisherman's boat. |
| **Safety Thresholds** | Fixed, binary regional indices based on general boat classes. | **Continuous Critical Beam Calculations:** Calculates $4 \times H_s$ dynamically for each coordinate. | Proactive notifications warning if local wave heights exceed the specific boat's stability limit. |
| **Spatial Granularity** | District-level polygons (entire district color-coded green, orange, or red). | **Point-Specific Coordinate Grid Risk:** Computes BSI and wave risks on a 500m coordinate resolution. | Highly localized micro-routing; a vessel can navigate safe channels even if a district is under caution. |
| **Explainability** | Shows colored map regions with generic warning text ("Boats should not sail"). | **Explainable BSI Decomposition:** Explains the physical wave-forcing vectors (steepness, crossing sea, wind-sea). | Builds trust with users and Coast Guard authorities by citing the mathematical reason for danger. |
| **Pathfinding & Routing** | None. (Users must visually interpret the colored map to plan their own coordinates). | **Marine Risk-Aware Route Optimization:** Pathfinding (A*) prioritizing safety over geographical straight lines. | Direct decision-support; routes vessels around storms, international borders, and MPAs. |
| **Temporal Planning** | Shows daily forecasts up to 3 or 10 days. | **Safest Departure Window Simulator:** Analyzes wave and wind dynamics across the planned trip duration. | Proposes the optimal time to leave port (e.g. *"Delay departure by 2 hours to avoid peak breakers"*). |
| **Scenario Simulation** | None. | **"What-If" Analysis:** Simulates route risk for alternate times, alternative speeds, and routes. | Allows ports and vessel owners to run safety simulations prior to dispatching trawlers. |
| **Feedback Loop** | Manual offline surveys or NGO collection. | **Digital Feedback & Continuous Model Refining:** Digital logging of sailor-reported conditions and outcomes. | Modern ML logging system for threshold updates and false-alarm correction. |
| **Offshore Borders** | None. | **PostGIS Geofencing:** Real-time checking against international maritime boundaries and MPAs. | Pre-warning prior to crossing international boundaries, preventing detentions. |
| **Outreach** | SMS, website, or mobile app overlays. | **Multilingual Voice-First Interface:** Offline-capable React dashboard with Web Speech API audio advisories. | Low-literacy accessible; reads alerts out loud in coastal languages (Hindi, Marathi, Bengali, Odia). |
