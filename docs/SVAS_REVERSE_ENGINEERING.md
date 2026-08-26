# INCOIS SVAS Technical Reverse Engineering

This document details the reverse engineering of the INCOIS Small Vessel Advisory and Forecast Services System (SVAS) based on live endpoints, browser-based network inspections, and the foundational scientific paper.

---

## 1. INCOIS Live Endpoints & Resources

### Public Interface
*   **Live Website:** `https://www.incois.gov.in/oceanservices/SVAS/index.html`
*   **Service Overview:** `https://www.incois.gov.in/site/services/SVA_overview.jsp`

### Live Data Feeds
*   **Animation Forecast GeoJSON (Points):** `https://www.incois.gov.in/oceanservices/SVAS/SVAS_Animation.geojson`
    *   *Description:* Contains coordinates (MultiPoints) of forecasted overturning zones for each day and BSI combination.
*   **Advisory District GeoJSON (Polygons):** `https://www.incois.gov.in/oceanservices/SVAS/SVAS_Advisory.geojson`
    *   *Description:* Contains coastal district spatial polygons with localized warnings, colors, and administrative metadata.

---

## 2. GeoJSON Schema Analysis

### A. Animation GeoJSON (`SVAS_Animation.geojson`)
*   **CRS:** `urn:ogc:def:crs:OGC:1.3:CRS84` (Standard WGS84 Longitude/Latitude order).
*   **Geometry Type:** `MultiPoint`
*   **Feature Properties:**
    *   `val` (Integer): Represents the warning/BSI risk class (e.g. `4` for rapid development, `6` for crossing sea + rapid dev, `7` for all indices exceeded).
    *   `day` (String): Forecast day index (`"1"` = Day 1, `"2"` = Day 2, etc.).
    *   `Date` (String): Forecast calendar date in `DD-MM-YYYY` format.
    *   `Count` (Integer): The count of spatial points associated with this feature.

### B. Advisory GeoJSON (`SVAS_Advisory.geojson`)
*   **Geometry Type:** `Polygon` / `MultiPolygon`
*   **Feature Properties:**
    *   `FID_Coasta` (Integer): Primary key indicator.
    *   `DistrictNa` / `name` / `ENG` (String): The name of the coastal district (e.g. `Kozhikode`, `Konaseema`).
    *   `state` (String): The coastal state of India (e.g. `Kerala`, `Andhra Pradesh`).
    *   `Color` (String): Color code representing warning status (`Red` for Warning, `Orange` for Alert, `Green` for Safe).
    *   `Advisory_E` (String): English advisory text.
    *   `Advisory_Local` (String): Local language translation of the advisory.

### C. Visual Mapping & User Interface Elements (from Live UI Inspection)
*   **Buffer Zones:** The map draws distance-specific coastal buffer stripes extending offshore (e.g. `Puri district (0-95)km`, `Puri district (0-20)km`) corresponding to wave-breaking and capsizing hazard distances.
*   **Legend Indicators:**
    *   `Alert` (Orange): Conditions exceed safety limits for the selected boat class.
    *   `Safe` (Green): Standard operating conditions.
*   **Controls:**
    *   `Animation` Checkbox: Triggers a temporal loop cycling through forecast Day-1, Day-2, and Day-3 coordinates.
    *   `Distance-wise Advisories` Checkbox: Toggles display of the coastal polygon hazard strips.
*   **Popups:** Triggered by left-clicking a district polygon. Displays the District Name, issue date, target boat width category, and daily forecast text detailing safe boundaries.

---

## 3. Scientific Baseline Equations & Thresholds

From the journal paper (*"Development of small vessel advisory and forecast services system for safe navigation and operations at sea"*, Journal of Operational Oceanography, 2022), the risk is calculated using three indicators:

### 1. Steepness Index ($I_{steepness}$)
Evaluates the instability caused by high and steep waves:
$$I_{steepness} = \frac{S_s}{0.05} \times \frac{H_s}{h_0}$$
*   $S_s$: Significant wave steepness.
*   $H_s$: Significant wave height.
*   $h_0$: Fixed constant ($2.5\text{ m}$ for Indian seas).
*   **Warning Threshold:** $I_{steepness} \ge 0.8$.

### 2. Crossing Sea Index ($I_{crossing}$)
Evaluates rolling hazards from multiple wave trains approaching from different directions:
$$I_{crossing} = \frac{1}{2} \times H_s \times e^{-10(s_s - 1)^2}$$
*   $s_s$: Directional spread parameter (ranges from $0$ to $\sqrt{2}$).
*   **Warning Threshold:** $I_{crossing} \ge 0.65$.

### 3. Rapid Development of Sea ($Z_{6h}$)
Evaluates sudden shifts in wind-sea conditions, reducing reaction time for small crafts:
$$Z_{6h} = \frac{|H_{sea\_i} - H_{sea\_f}|}{H_{sea\_i}}$$
*   $H_{sea\_i}$: Wind-sea wave height at initial time.
*   $H_{sea\_f}$: Wind-sea wave height 6 hours later.
*   **Warning Threshold:** $Z_{6h} \ge 0.2$ (meaning $\ge 20\%$ wave height increase in 6 hours).

---

## 4. Boat Safety Index (BSI) Mapping

The BSI aggregates the three indices using a bit-weighted sum:
$$\text{BSI} = S_{steepness} + S_{crosssea} + S_{rapiddev}$$
Where:
*   $S_{steepness} = 1$ if $I_{steepness} \ge 0.8$ else $0$.
*   $S_{crosssea} = 2$ if $I_{crossing} \ge 0.65$ else $0$.
*   $S_{rapiddev} = 4$ if $Z_{6h} \ge 0.2$ else $0$.

### BSI Values & Contributions:
| BSI | $S_{rapiddev}$ (4) | $S_{crosssea}$ (2) | $S_{steepness}$ (1) | Physical Risk Cause |
| :--- | :---: | :---: | :---: | :--- |
| **0** | 0 | 0 | 0 | **SAFE** (No warning thresholds exceeded) |
| **1** | 0 | 0 | 1 | Elevated wave steepness only |
| **2** | 0 | 1 | 0 | Crossing sea waves only (rolling danger) |
| **3** | 0 | 1 | 1 | Elevated steepness + Crossing sea |
| **4** | 1 | 0 | 0 | Rapid development of sea only |
| **5** | 1 | 0 | 1 | Rapid development + wave steepness |
| **6** | 1 | 1 | 0 | Rapid development + Crossing sea |
| **7** | 1 | 1 | 1 | **CRITICAL** (All three wave hazards active) |

---

## 5. Daily Advisory Classification Logic
The original paper converts 8 consecutive 3-hourly time steps (24 hours) into daily warnings:
1.  **WARNING:** BSI is non-zero for at least 7 out of 8 time steps.
2.  **ALERT:** BSI is non-zero at any step from the 5th through the 8th time steps.
3.  **SAFE:** Not matching WARNING or ALERT conditions.

---

## 6. Boat-Specific Sizing Vulnerability
A core component of the BSI model is that a sea state is not universally dangerous. A small craft is highly vulnerable under waves that a large mechanized trawler handles safely:
$$\text{Critical Beam} = 4 \times H_s$$
If a vessel's beam is less than the $\text{Critical Beam}$, it is flagged as **Vulnerable** (high capsizing probability) for that cell.

---

## 7. Gaps & Improvements (Live System vs. Our Platform)

*   **Spatial Granularity:** Existing SVAS shows district-level polygons. Our platform calculates coordinate-specific safety thresholds.
*   **Vessel Specifics:** Existing SVAS uses 3 static categories ($<4$m, $<6$m, $<7$m). Our platform accepts a continuous profile (e.g. $3.2$m beam) to calculate individual safety coefficients.
*   **Explanation:** Live SVAS shows a colored map with a static generic message. Our system decomposes BSI into its physical causes (e.g., *"Rough crossing waves combined with sudden wind-sea development"*).
