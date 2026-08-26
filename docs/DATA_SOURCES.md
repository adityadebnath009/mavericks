# Data Sources Reference

This document details the official INCOIS oceanographic and meteorological datasets integrated into the ORCA Portal system.

---

## 1. WaveWatch III Wave Forecast Dataset

*   **Dataset Identifier:** `rsmc_combined_ww3_20260825.nc`
*   **Purpose:** Wave state parameters (height, direction, period, steepness) for SVAS Boat Safety Index (BSI) calculation.
*   **WMS Metadata Endpoint:** 
    `https://www.incois.gov.in/thredds/wms/osf/ww3/rsmc_combined_ww3_20260825.nc?request=GetCapabilities&service=WMS&version=1.1.1`
*   **OPENDAP Data Endpoint:**
    `https://www.incois.gov.in/thredds/dodsC/osf/ww3/rsmc_combined_ww3_20260825.nc`
*   **NetCDF Subset Service (NCSS):**
    `https://www.incois.gov.in/thredds/ncss/grid/osf/ww3/rsmc_combined_ww3_20260825.nc`
*   **HTTP Direct Download:**
    `https://www.incois.gov.in/thredds/fileServer/osf/ww3/rsmc_combined_ww3_20260825.nc`

### Metadata Schema
*   **Variables:**
    *   `HS`: Significant Wave Height (\(m\))
    *   `STP`: Significant Wave Steepness (\(HS/LM\), dimensionless)
    *   `LM`: Mean Wave Length (\(m\))
    *   `T02`: Mean Period Tz (\(s\))
    *   `MWD`: Mean Wave Direction (\(deg\))
    *   `PWD`: Principle Wave Direction (\(deg\))
    *   `DIR`: Mean Wave Direction (\(rad\))
    *   `SPR`: Directional Spread (clashing spread parameter, ranges from 0 to \(\sqrt{2}\))
    *   `DP`: Peak Wave Direction (\(rad\))
    *   `UWND`: Eastward wind speed component (\(m/s\))
    *   `VWND`: Northward wind speed component (\(m/s\))
*   **Dimensions:**
    *   `TIME`: Length = 56 steps.
    *   `IOYAXIS` (Latitude): Length = 901 grid points.
    *   `IOXAXIS` (Longitude): Length = 901 grid points.
*   **Spatial Resolution:** \(0.1^\circ \times 0.1^\circ\) (approx. 11 km grid size).
*   **Spatial Coverage:**
    *   Latitude: \(-60.0^\circ\text{ S}\) to \(30.0^\circ\text{ N}\)
    *   Longitude: \(30.0^\circ\text{ E}\) to \(120.0^\circ\text{ E}\)
*   **Temporal Resolution:** 3-hourly intervals (`PT3H` on the hour).
*   **Forecast Coverage:** 7 days (e.g. `2026-08-26T00:00:00Z` to `2026-09-01T21:00:00Z`).

---

## 2. NIO Ocean Currents Forecast Dataset

*   **Dataset Identifier:** `CURRENTS_NIO_20260824.nc`
*   **Purpose:** Ocean current velocities for vessel operational safety and route optimization cost modeling.
*   **WMS Metadata Endpoint:**
    `https://www.incois.gov.in/thredds/wms/osf/currents/CURRENTS_NIO_20260824.nc?request=GetCapabilities&service=WMS&version=1.1.1`
*   **OPENDAP Data Endpoint:**
    `https://www.incois.gov.in/thredds/dodsC/osf/currents/CURRENTS_NIO_20260824.nc`
*   **NetCDF Subset Service (NCSS):**
    `https://www.incois.gov.in/thredds/ncss/grid/osf/currents/CURRENTS_NIO_20260824.nc`
*   **HTTP Direct Download:**
    `https://www.incois.gov.in/thredds/fileServer/osf/currents/CURRENTS_NIO_20260824.nc`

### Metadata Schema
*   **Variables:**
    *   `U`: Eastward surface current velocity component (\(m/s\))
    *   `V`: Northward surface current velocity component (\(m/s\))
    *   `CURRENT`: Surface currents magnitude/speed (\(m/s\))
*   **Dimensions:**
    *   `TAXIS` (Time): Length = 32 steps.
    *   `DEPTH1_1` (Depth): Length = 1 step (value = 0.0m, representing surface current).
    *   `LAT` (Latitude): Length = 720 grid points.
    *   `LON` (Longitude): Length = 1080 grid points.
*   **Spatial Resolution:** \(1/12^\circ\) (approx. \(0.0833^\circ\) or 9 km grid size).
*   **Spatial Coverage:**
    *   Latitude: \(-30.0^\circ\text{ S}\) to \(29.8927^\circ\text{ N}\)
    *   Longitude: \(30.0^\circ\text{ E}\) to \(119.8807^\circ\text{ E}\)
*   **Temporal Resolution:** 3-hourly intervals (`PT3H` offset by 1.5 hours: e.g., 01:30, 04:30, 07:30).
*   **Forecast Coverage:** 4 days (e.g. `2026-08-25T01:30:00Z` to `2026-08-28T22:30:00Z`).

---

## 3. Subsetting & Alignment Strategy

*   **Spatial Grid Association:** Both datasets share a common bounding box over the Northern Indian Ocean (NIO) coordinates. Because the currents dataset (\(1/12^\circ\)) has a slightly higher spatial resolution than the WW3 dataset (\(0.1^\circ\)), nearest-neighbor mapping is applied to pair wave and current parameters at any coordinate.
*   **Temporal Offset:** The WW3 forecast is sampled on the hour (e.g. 12:00:00), whereas the Currents forecast is sampled on the half-hour (e.g. 13:30:00). We align the two datasets temporally by matching each WW3 timestamp with the nearest available Currents timestamp (producing an offset of exactly \(\pm 1.5\) hours).
