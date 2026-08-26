# Data Pipeline Architecture

This document describes the flow and alignment of INCOIS forecast datasets inside the ORCA Portal system.

---

## Data Flow Diagram

```text
                ┌── WW3 NetCDF (rsmc_combined_ww3_20260825.nc)
                │
INCOIS THREDDS ─┤
                │
                └── NIO Currents NetCDF (CURRENTS_NIO_20260824.nc)
                         ↓
                 Spatial/Temporal Alignment
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
         SVAS BSI              Current Risk
              ↓                     ↓
              └──────────┬──────────┘
                         ↓
                   ORCA Risk Model
                         ↓
                  Advisory / Routing
```

---

## 1. INCOIS THREDDS Server Querying
The portal queries the remote INCOIS THREDDS catalog using the **OPENDAP protocol** via python libraries `xarray` and `netCDF4`. 

Rather than downloading large NetCDF datasets (over 600 MB each) to the local environment, the backend dynamically queries sliced coordinates on-demand, fetching only a few kilobytes of data required for the vessel's coordinates and inspection timestamps.

---

## 2. Spatial & Temporal Alignment
*   **Spatial Mapping:** Uses nearest-neighbor grid point matching. A target coordinate `(lat, lon)` is mapped to `IOYAXIS/IOXAXIS` in WW3 and `LAT/LON` in Currents.
*   **Temporal Matching:** Matches time arrays from `TIME` (WW3) and `TAXIS` (Currents). Since Currents has a \(\pm 1.5\) hours offset relative to WW3 timestamps, alignment maps each hourly wave step to the closest half-hourly currents step.

---

## 3. Risk Separation Constraint
*   **SVAS BSI Engine:** The wave-steepness, crossing-sea, and rapid-sea-development indicators are calculated strictly according to the official SVAS parameters. BSI scores are kept independent of currents.
*   **Current Risk / Routing Cost:** Surface current speed and directions derived from U/V components are analyzed as a separate operational safety layer. They feed into routing costs for pathfinding, without modifying the standard SVAS BSI formula.
*   **ORCA Risk Model:** Combines BSI and Currents warnings logically inside the UI layout to advise safety without violating scientific formulas.
