# SVAS Boat Safety Index (BSI) Methodology

This document outlines the official scientific equations, thresholds, and mappings of the INCOIS Small Vessel Advisory Service (SVAS) Boat Safety Index (BSI), as verified against the baseline paper.

---

## 1. Safety Threshold Equations

The BSI is calculated at any given location and timestamp by evaluating three independent wave-forcing risk indices:

### A. Steepness Index (\(I_{steepness}\))
Evaluates capsizing dangers caused by short, steep waves:
\[I_{steepness} = \frac{S_s}{0.05} \times \frac{H_s}{h_0}\]
*   \(S_s\): Significant wave steepness (dimensionless, \(HS/LM\)).
*   \(H_s\): Significant wave height (\(m\)).
*   \(h_0\): Safe reference wave height constant (\(2.5\text{ m}\) for Indian seas).
*   **Warning Exceeded:** \(I_{steepness} \ge 0.8\).

### B. Crossing Sea Index (\(I_{crossing}\))
Evaluates severe rolling hazards from waves approaching from multiple clashing angles:
\[I_{crossing} = \frac{1}{2} \times H_s \times e^{-10(s_s - 1)^2}\]
*   \(H_s\): Significant wave height (\(m\)).
*   \(s_s\): Directional spread parameter (ranges from \(0\) to \(\sqrt{2}\)).
*   **Warning Exceeded:** \(I_{crossing} \ge 0.65\).

### C. Rapid Development of Sea (\(Z_{6h}\))
Evaluates rapid wind-wave growth that limits navigation/reaction time for small vessels:
\[Z_{6h} = \frac{|H_{sea\_f} - H_{sea\_i}|}{H_{sea\_i}}\]
*   \(H_{sea\_i}\): **Wind Sea wave height** at the start of a 6-hour lookback period. Mapped directly to **`PHS00`** from the INCOIS WW3 dataset.
*   \(H_{sea\_f}\): **Wind Sea wave height** at the current forecast timestamp. Mapped to **`PHS00`**.
*   **Warning Exceeded:** \(Z_{6h} \ge 0.2\) (representing a \(\ge 20\%\) wave growth in 6 hours).
*   **Important:** Total significant wave height \(H_s\) must *never* be substituted for \(H_{sea}\).

---

## 2. Bitwise BSI Calculation

The final BSI value is computed as a bitwise summation:
\[\text{BSI} = S_{rapiddev} (4) + S_{crosssea} (2) + S_{steepness} (1)\]
Where each flag is \(1\) if the corresponding threshold is exceeded, and \(0\) otherwise.

### Risk Class Definitions:
*   **BSI = 0:** **SAFE** (No warning thresholds exceeded).
*   **BSI = 1:** Steepness warning exceeded.
*   **BSI = 2:** Crossing sea warning exceeded.
*   **BSI = 3:** Steepness + Crossing sea warning.
*   **BSI = 4:** Rapid sea development warning.
*   **BSI = 5:** Rapid development + Steepness.
*   **BSI = 6:** Rapid development + Crossing sea.
*   **BSI = 7:** **CRITICAL** (All three wave indices exceeded).

---

## 3. Daily Aggregation Logic
A daily advisory is compiled over 8 consecutive 3-hourly steps (24 hours):
1.  **WARNING:** BSI \(\ge 1\) for at least 7 out of 8 steps.
2.  **ALERT:** BSI \(\ge 1\) during any of the late afternoon/night steps (steps 5 to 8).
3.  **SAFE:** Standard operating conditions (does not meet WARNING or ALERT criteria).
