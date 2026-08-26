# INCOIS Data Dictionary

This data dictionary details the variables, dimensions, attributes, and physical meanings of the INCOIS NetCDF forecast datasets integrated into the ORCA Portal system.

---

## 1. WaveWatch III Wave Forecast Dataset

*   **Dataset URL:** `https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_20260825.nc`
*   **Dimensions:**
    *   `TIME`: Length = 56 steps. Represents 3-hourly forecast steps starting at `2026-08-26T00:00:00Z` to `2026-09-01T21:00:00Z`.
    *   `IOYAXIS` (Latitude): Length = 901 grid points. Range: \(-60.0^\circ\text{ S}\) to \(30.0^\circ\text{ N}\).
    *   `IOXAXIS` (Longitude): Length = 901 grid points. Range: \(30.0^\circ\text{ E}\) to \(120.0^\circ\text{ E}\).

### Variable Specifications
| NetCDF Name | WMS Name | Long Name / Description | Units | Physical Meaning & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`HS`** | `HS` | Wave height (m) | meters | Significant Wave Height (\(H_s\)). Used in capsizing risk and BSI steepness/crossing indices. |
| **`STP`** | `STP` | Wave Steepness (HS/LM) | dimensionless | Wave steepness index (\(S_s\)). Used in BSI steepness calculation. |
| **`SPR`** | `SPR` | Dir. spread | dimensionless | Directional spread (\(s_s\)). Range: \(0\) to \(\sqrt{2}\). Used to identify crossing sea/clashing waves. |
| **`T02`** | `T02` | Mean Per Tz (s) | seconds | Mean zero-upcrossing wave period (\(T_z\)). |
| **`MWD`** | `MWD` | Mean Wave Direction (Deg) | degrees | Mean direction from which waves travel. |
| **`PHS00`** | `PHS00` | Part. Hs (m) | meters | **Wind Sea Wave Height (\(H_{sea}\))**. Corresponds to Partition 0 Wave Height (shorter period, positively correlated with wind speed). Used in BSI rapid development (\(Z_{6h}\)). |
| **`PHS01`** | `PHS01` | Part. Hs (m) | meters | Swell Wave Height. Corresponds to Partition 1 Wave Height (longer period, negatively correlated with local wind speed). |
| **`UWND`** | `UWND` | Wind U (m/s) | m/s | Eastward wind velocity component. |
| **`VWND`** | `VWND` | Wind V (m/s) | m/s | Northward wind velocity component. |

---

## 2. NIO Surface Currents Dataset

*   **Dataset URL:** `https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_20260824.nc`
*   **Dimensions:**
    *   `TAXIS` (Time): Length = 32 steps. Represents 3-hourly forecast steps starting at `2026-08-25T01:30:00Z` to `2026-08-28T22:30:00Z`. Note the 1.5-hour offset from the WW3 dataset.
    *   `DEPTH1_1` (Depth): Length = 1 step (value = 0.0m). Represents surface current.
    *   `LAT` (Latitude): Length = 720 grid points. Range: \(-30.0^\circ\text{ S}\) to \(29.8927^\circ\text{ N}\).
    *   `LON` (Longitude): Length = 1080 grid points. Range: \(30.0^\circ\text{ E}\) to \(119.8807^\circ\text{ E}\).

### Variable Specifications
| NetCDF Name | WMS Name | Long Name / Description | Units | Physical Meaning & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`U`** | `U` | U Component | m/s | Eastward current velocity component. |
| **`V`** | `V` | V Component | m/s | Northward current velocity component. |
| **`CURRENT`** | `CURRENT` | Surface Currents (m/s) | m/s | Magnitudes/speed of surface currents (also derivable as \(\sqrt{U^2 + V^2}\)). |
