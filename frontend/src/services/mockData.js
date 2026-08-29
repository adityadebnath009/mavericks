/**
 * Navik Marine Intelligence Platform - High-Fidelity Mock & Fallback Datasets
 * Adheres strictly to Frozen Navik Design System and INCOIS / PostGIS schemas.
 */

// 1. Pre-configured Major Indian Ports & Naval Bases
export const MOCK_PORTS = [
  { id: 'mumbai', name: 'Mumbai Harbour (MH)', lat: 18.9220, lon: 72.8347, region: 'West Coast' },
  { id: 'kochi', name: 'Kochi Naval Base (KL)', lat: 9.9656, lon: 76.2625, region: 'South-West' },
  { id: 'vizag', name: 'Visakhapatnam Port (AP)', lat: 17.6868, lon: 83.2185, region: 'East Coast' },
  { id: 'chennai', name: 'Chennai Port (TN)', lat: 13.0827, lon: 80.2707, region: 'South-East' },
  { id: 'mangalore', name: 'New Mangalore Port (KA)', lat: 12.9141, lon: 74.8560, region: 'West Coast' },
  { id: 'porbandar', name: 'Porbandar Coast Guard (GJ)', lat: 21.6417, lon: 69.6293, region: 'North-West' },
  { id: 'port_blair', name: 'Port Blair Harbour (AN)', lat: 11.6234, lon: 92.7265, region: 'Andaman Sea' },
  { id: 'kavaratti', name: 'Kavaratti Base (LD)', lat: 10.5669, lon: 72.6420, region: 'Lakshadweep' },
  { id: 'paradip', name: 'Paradip Port (OD)', lat: 20.3167, lon: 86.6111, region: 'East Coast' },
  { id: 'tuticorin', name: 'V.O.C. Port Tuticorin (TN)', lat: 8.7642, lon: 78.1348, region: 'Gulf of Mannar' }
];

// 2. Mock Indian EEZ Boundaries & Marine Protected Areas (MPAs)
export const MOCK_GEOFENCE_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        type: 'EEZ',
        name: 'Indian Exclusive Economic Zone (EEZ) Boundary'
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [68.1, 23.7], [67.5, 22.0], [66.0, 20.0], [65.5, 18.0],
          [66.5, 15.0], [68.0, 12.0], [70.0, 9.0], [72.0, 6.5],
          [75.0, 4.5], [77.5, 5.0], [80.0, 6.0], [83.0, 8.5],
          [86.0, 12.0], [89.0, 15.5], [90.5, 18.0], [89.2, 21.5]
        ]
      }
    },
    {
      type: 'Feature',
      properties: {
        type: 'MPA',
        name: 'Gulf of Mannar Marine National Park'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.8, 9.2], [79.3, 9.3], [79.4, 9.0], [78.9, 8.8], [78.8, 9.2]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        type: 'MPA',
        name: 'Sundarbans Marine Biosphere Reserve'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [88.5, 21.8], [89.2, 21.8], [89.1, 21.3], [88.4, 21.4], [88.5, 21.8]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        type: 'MPA',
        name: 'Gahirmatha Marine Sanctuary (Olive Ridley)'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [86.8, 20.8], [87.2, 20.9], [87.1, 20.4], [86.7, 20.5], [86.8, 20.8]
        ]]
      }
    },
    {
      type: 'Feature',
      properties: {
        type: 'MPA',
        name: 'Malvan Marine Sanctuary'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [73.4, 16.1], [73.5, 16.1], [73.5, 15.9], [73.4, 15.9], [73.4, 16.1]
        ]]
      }
    }
  ]
};

// 3. Mock Potential Fishing Zone (PFZ) Vector Lines
export const MOCK_PFZ_LINES = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 'pfzlines.1',
      properties: {
        id: 'pfzlines.1',
        name: 'Konkan Shelf Front Alpha',
        validity: '2026-08-29',
        sst_median: 28.4,
        chl_median: 0.45,
        current_median: 0.35,
        wave_hs_median: 1.20,
        wind_speed_median: 18.5,
        catch_score: 92
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [72.45, 19.12], [72.60, 19.35], [72.75, 19.55], [72.85, 19.80]
        ]
      }
    },
    {
      type: 'Feature',
      id: 'pfzlines.2',
      properties: {
        id: 'pfzlines.2',
        name: 'Andhra Offshore Upwelling Beta',
        validity: '2026-08-29',
        sst_median: 27.9,
        chl_median: 0.62,
        current_median: 0.42,
        wave_hs_median: 1.45,
        wind_speed_median: 21.0,
        catch_score: 88
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [84.60, 17.30], [84.90, 17.55], [85.20, 17.80], [85.45, 18.05]
        ]
      }
    },
    {
      type: 'Feature',
      id: 'pfzlines.3',
      properties: {
        id: 'pfzlines.3',
        name: 'Malabar Coastal Convergence Gamma',
        validity: '2026-08-29',
        sst_median: 28.8,
        chl_median: 0.55,
        current_median: 0.28,
        wave_hs_median: 1.10,
        wind_speed_median: 16.0,
        catch_score: 84
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [75.80, 9.80], [76.05, 10.15], [76.25, 10.45], [76.40, 10.75]
        ]
      }
    },
    {
      type: 'Feature',
      id: 'pfzlines.4',
      properties: {
        id: 'pfzlines.4',
        name: 'Saurashtra Thermal Gradient Delta',
        validity: '2026-08-29',
        sst_median: 27.6,
        chl_median: 0.40,
        current_median: 0.48,
        wave_hs_median: 1.60,
        wind_speed_median: 24.5,
        catch_score: 79
      },
      geometry: {
        type: 'LineString',
        coordinates: [
          [69.20, 21.20], [69.45, 21.45], [69.70, 21.70]
        ]
      }
    }
  ]
};

// 4. Mock 0.4° BSI Safety Grid FeatureCollection
export const MOCK_GRID_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // Mumbai Offshore Grid Cells
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [[[72.4, 18.8], [72.8, 18.8], [72.8, 19.2], [72.4, 19.2], [72.4, 18.8]]]
      },
      properties: {
        bsi: 1,
        hs: 1.2,
        wind_speed_kmh: 18.5,
        current_speed_ms: 0.35,
        wind_dir_deg: 215.0,
        current_dir_deg: 112.0,
        center_lat: 19.0,
        center_lon: 72.6,
        color: 'green'
      }
    },
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [[[72.0, 18.8], [72.4, 18.8], [72.4, 19.2], [72.0, 19.2], [72.0, 18.8]]]
      },
      properties: {
        bsi: 2,
        hs: 1.6,
        wind_speed_kmh: 22.0,
        current_speed_ms: 0.45,
        wind_dir_deg: 220.0,
        current_dir_deg: 120.0,
        center_lat: 19.0,
        center_lon: 72.2,
        color: 'yellow'
      }
    },
    // Kochi Offshore Grid Cells
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [[[75.8, 9.6], [76.2, 9.6], [76.2, 10.0], [75.8, 10.0], [75.8, 9.6]]]
      },
      properties: {
        bsi: 1,
        hs: 1.1,
        wind_speed_kmh: 15.0,
        current_speed_ms: 0.30,
        wind_dir_deg: 240.0,
        current_dir_deg: 160.0,
        center_lat: 9.8,
        center_lon: 76.0,
        color: 'green'
      }
    },
    // Visakhapatnam Offshore Grid Cells
    {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [[[83.2, 17.4], [83.6, 17.4], [83.6, 17.8], [83.2, 17.8], [83.2, 17.4]]]
      },
      properties: {
        bsi: 1,
        hs: 1.2,
        wind_speed_kmh: 17.8,
        current_speed_ms: 0.38,
        wind_dir_deg: 190.0,
        current_dir_deg: 75.0,
        center_lat: 17.6,
        center_lon: 83.4,
        color: 'green'
      }
    }
  ]
};

// 5. Mock Coastal District Advisories
export const MOCK_ADVISORIES_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        DistrictNa: 'Mumbai Suburban',
        state: 'Maharashtra',
        Color4: 'green',
        Color6: 'green',
        Color7: 'green',
        ENG4: 'Mumbai Suburban (0-15km): Sea conditions optimal. Motorized small crafts (<4m) can safely sail.',
        ENG6: 'Mumbai Suburban: Trawlers (<6m) can safely navigate coastal fishing grounds.',
        ENG7: 'Mumbai Suburban: Deep-sea vessels (<7m) can operate safely.',
        HIN4: 'मुंबई उपनगर: 4 मीटर से छोटी नौकाएं सुरक्षित नौकायन कर सकती हैं।',
        MAR4: 'मुंबई उपनगर: 4 मीटर पेक्षा कमी रुंदीच्या बोटी सुरक्षितपणे प्रवास करू शकतात.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[[72.7, 19.0], [72.9, 19.0], [72.9, 19.3], [72.7, 19.3], [72.7, 19.0]]]
      }
    },
    {
      type: 'Feature',
      properties: {
        DistrictNa: 'Kozhikode',
        state: 'Kerala',
        Color4: 'orange',
        Color6: 'green',
        Color7: 'green',
        ENG4: 'Kozhikode district (0-5km): Elevated swell period. Boats less than 4m wide should exercise caution.',
        ENG6: 'Kozhikode district: Boats less than 6m wide can safely sail.',
        ENG7: 'Kozhikode district: Boats less than 7m wide can safely sail.',
        HIN4: 'कोझिकोड: 4 मीटर से छोटी नौकाएं सावधानी बरतें।',
        MAR4: 'कोझिकोडे: 4 मीटर पेक्षा कमी रुंदीच्या बोटींनी सावधगिरी बाळगावी.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[[75.7, 11.1], [75.9, 11.1], [75.9, 11.4], [75.7, 11.4], [75.7, 11.1]]]
      }
    }
  ]
};

// 6. Mock 24-Hour Diurnal Timeline Forecast
export const MOCK_FORECAST_TIMELINE = [
  { time: '00:00', bsi: 1, wave_height: 1.1, wind_speed: 15.2, current_speed: 0.30 },
  { time: '03:00', bsi: 1, wave_height: 1.2, wind_speed: 16.0, current_speed: 0.32 },
  { time: '06:00', bsi: 1, wave_height: 1.3, wind_speed: 17.4, current_speed: 0.35 },
  { time: '09:00', bsi: 1, wave_height: 1.2, wind_speed: 18.1, current_speed: 0.34 },
  { time: '12:00', bsi: 1, wave_height: 1.2, wind_speed: 18.5, current_speed: 0.35 },
  { time: '15:00', bsi: 1, wave_height: 1.1, wind_speed: 17.0, current_speed: 0.33 },
  { time: '18:00', bsi: 1, wave_height: 1.0, wind_speed: 15.5, current_speed: 0.31 },
  { time: '21:00', bsi: 0, wave_height: 0.9, wind_speed: 14.2, current_speed: 0.28 }
];

// 7. Mock Point Safety Assessment Data
export const MOCK_SAFETY_DATA = {
  rating: 'SAFE',
  recommendation: 'Safe to venture into sea. Exercise standard maritime caution.',
  reasons: [
    'All weather, wave, current, and geofence parameters are within optimal safety ranges.'
  ],
  vessel_suitability: {
    vessel_beam_m: 3.5,
    critical_beam_m: 4.8,
    vulnerable: false
  },
  bsi_metrics: {
    bsi_score: 1,
    rating: 'SAFE',
    description: 'All wave-forcing indicators within safe parameters.',
    wave_steepness: 0.012,
    directional_spread: 0.24
  },
  raw_metrics: {
    wave_height_m: 1.2,
    wind_speed_kmh: 18.5,
    current_speed_ms: 0.35,
    distance_to_border_km: 116.97,
    is_inside_eez: true,
    is_inside_mpa: false,
    mpa_name: null,
    inspect_hs: 1.2,
    inspect_stp: 0.012,
    inspect_spr: 0.24,
    inspect_hsea: 0.8,
    inspect_t02: 6.5,
    inspect_mwd: 210,
    inspect_wind: 18.5,
    inspect_curr: 0.35,
    peak_wind_time: '26 Aug • 12:00 UTC',
    peak_curr_time: '26 Aug • 12:00 UTC',
    peak_wave_time: '26 Aug • 12:00 UTC',
    incois_sst: 28.4,
    incois_chl: 0.215
  },
  navik_risk: {
    overall_status: 'LOW',
    wind_risk: 'LOW',
    current_risk: 'LOW',
    geofence_risk: 'CLEAR'
  },
  orca_risk: {
    overall_status: 'LOW',
    wind_risk: 'LOW',
    current_risk: 'LOW',
    geofence_risk: 'CLEAR'
  },
  coordinates: {
    latitude: 17.431,
    longitude: 84.703
  },
  provenance: {
    source: 'INCOIS Ocean State Forecast (Offline Mock)',
    ww3_dataset: 'rsmc_combined_ww3_20260825.nc',
    currents_dataset: 'CURRENTS_NIO_20260824.nc',
    retrieved_at: '26 Aug 2026 • 12:00 UTC',
    daily_bsi_forecast: {
      day1: { score: 1, rating: 'SAFE' },
      day2: { score: 1, rating: 'SAFE' },
      day3: { score: 2, rating: 'SAFE' }
    }
  }
};

// 8. Mock Route Calculation Data
export const MOCK_ROUTE_DATA = {
  route_coords: [
    [72.8347, 18.9220],
    [72.7100, 18.9800],
    [72.5800, 19.0600],
    [72.4500, 19.1200]
  ],
  straight_coords: [
    [72.8347, 18.9220],
    [72.4500, 19.1200]
  ],
  summary: {
    distance_km: 48.2,
    distance_nmi: 26.0,
    travel_time_hours: 2.6,
    max_bsi: 1,
    overall_risk: 'LOW',
    fuel_savings_est: '12%',
    avoided_hazards: [
      'Malvan Marine Sanctuary boundary preserved (>15km buffer)',
      'Circumvented coastal shoal area',
      'High-risk wave convergence zone bypassed'
    ]
  },
  alternate_route: {
    route_coords: [[72.8347, 18.9220], [72.4500, 19.1200]],
    distance_km: 43.5,
    distance_nmi: 23.5,
    travel_time_hours: 2.3,
    max_bsi: 2,
    overall_risk: 'MODERATE',
    hazard_warning: 'Crosses near shallow coastal breakwater'
  },
  comparison: {
    recommended: 'A* Safest & Current-Optimized Path',
    reason: '4.7 km longer than straight line, but avoids wave breaking zones and provides maximum hull stability.'
  }
};

// 9. Mock Data Telemetry Status
export const MOCK_DATA_STATUS = {
  incois_pfz: 'ONLINE',
  incois_svas: 'ONLINE',
  ww3_forecast: 'FORECAST',
  ocean_currents: 'FORECAST',
  imd_warnings: 'UNAVAILABLE',
  last_updated: '26 Aug 2026 • 12:00 UTC'
};

// 10. Helper: Generate Dynamic Curved Mock Route
export function generateMockRoute(start, end, beam = 3.5) {
  const sLat = start?.lat ?? 18.9220;
  const sLon = start?.lon ?? 72.8347;
  const eLat = end?.lat ?? 19.1200;
  const eLon = end?.lon ?? 72.4500;

  // Approximate great-circle distance
  const dLat = (eLat - sLat) * Math.PI / 180;
  const dLon = (eLon - sLon) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(sLat * Math.PI / 180) * Math.cos(eLat * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const straightDistKm = Math.max(5, Math.round(6371 * c * 10) / 10);
  const routeDistKm = Math.round(straightDistKm * 1.08 * 10) / 10;
  const travelTimeHrs = Math.round((routeDistKm / 18.52) * 10) / 10;

  // Generate 5 waypoint arc
  const routeCoords = [
    [sLon, sLat],
    [sLon + (eLon - sLon) * 0.25 - 0.04, sLat + (eLat - sLat) * 0.25 + 0.02],
    [sLon + (eLon - sLon) * 0.50 - 0.06, sLat + (eLat - sLat) * 0.50 + 0.03],
    [sLon + (eLon - sLon) * 0.75 - 0.03, sLat + (eLat - sLat) * 0.75 + 0.01],
    [eLon, eLat]
  ];

  return {
    route_coords: routeCoords,
    straight_coords: [[sLon, sLat], [eLon, eLat]],
    summary: {
      distance_km: routeDistKm,
      distance_nmi: Math.round((routeDistKm / 1.852) * 10) / 10,
      travel_time_hours: travelTimeHrs,
      max_bsi: beam < 4.0 ? 2 : 1,
      overall_risk: beam < 4.0 ? 'MODERATE' : 'LOW',
      fuel_savings_est: '9.4%',
      avoided_hazards: [
        'Circumvented coastal shallow bathymetry',
        'Maintained international EEZ safety corridor',
        'Avoided Marine Protected Area proximity buffer'
      ]
    },
    alternate_route: {
      route_coords: [[sLon, sLat], [eLon, eLat]],
      distance_km: straightDistKm,
      distance_nmi: Math.round((straightDistKm / 1.852) * 10) / 10,
      travel_time_hours: Math.round((straightDistKm / 18.52) * 10) / 10,
      max_bsi: 3,
      overall_risk: 'MODERATE'
    },
    comparison: {
      recommended: 'A* Optimized Safe Vector',
      reason: `${Math.round((routeDistKm - straightDistKm) * 10) / 10} km longer than direct bearing, but avoids shallow coastal shoals and reduces capsizing vulnerability.`
    }
  };
}

// 11. Helper: Generate Dynamic PFZ Evaluation
export function generateMockPfzEvaluation(vessel, pfzId = 'pfzlines.1', beam = 3.5) {
  const vLat = vessel?.lat ?? 18.96;
  const vLon = vessel?.lon ?? 72.82;
  const feature = MOCK_PFZ_LINES.features.find(f => f.id === pfzId) || MOCK_PFZ_LINES.features[0];
  const targetCoords = feature.geometry.coordinates[0];

  const dLat = (targetCoords[1] - vLat) * Math.PI / 180;
  const dLon = (targetCoords[0] - vLon) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(vLat * Math.PI / 180) * Math.cos(targetCoords[1] * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  const distanceKm = Math.round(6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));

  return {
    pfz_id: pfzId,
    distance_km: distanceKm,
    nearest_point: { latitude: targetCoords[1], longitude: targetCoords[0] },
    properties: feature.properties,
    marine_conditions: {
      wave_height_m: feature.properties.wave_hs_median ?? 1.20,
      wind_speed_kmh: feature.properties.wind_speed_median ?? 18.5,
      current_speed_ms: feature.properties.current_median ?? 0.35,
      wave_steepness: 0.013,
      directional_spread: 0.22,
      sst: feature.properties.sst_median ?? 28.4,
      chlorophyll: feature.properties.chl_median ?? 0.45
    },
    marine_risk: {
      rating: beam < 4.0 ? 'MODERATE' : 'LOW',
      reasons: ['Optimal sea surface temperature front and stable wave conditions at target zone.']
    },
    provenance: {
      source: 'INCOIS PFZ GeoServer WFS (Offline Mock)',
      validity: '2026-08-29'
    }
  };
}

// 12. Helper: Generate Point Analytics Telemetry
export function generateMockPointAnalytics(lat, lon) {
  const nLat = Number(lat) || 18.96;
  const nLon = Number(lon) || 72.82;
  const sst = Math.round((28.0 + Math.sin(nLat * 0.5 + nLon * 0.3) * 1.5) * 10) / 10;
  const chl = Math.round((0.45 + Math.cos(nLat * 0.4 + nLon * 0.2) * 0.2) * 100) / 100;
  const wind = Math.round((18.0 + Math.sin(nLon * 0.6) * 6.0) * 10) / 10;
  const curr = Math.round((0.35 + Math.cos(nLat * 0.5) * 0.15) * 100) / 100;
  const wave = Math.round((1.2 + Math.sin(nLat * 0.3 + nLon * 0.4) * 0.4) * 10) / 10;
  const bsi = wave > 2.5 || wind > 35 ? 3 : wave > 1.8 || wind > 25 ? 2 : 1;

  return {
    status: 'success',
    coordinates: {
      latitude: Math.round(nLat * 10000) / 10000,
      longitude: Math.round(nLon * 10000) / 10000
    },
    timestamp: new Date().toISOString(),
    source: 'INCOIS OPeNDAP & WaveWatch III (Offline Cache)',
    metrics: {
      sst_c: sst,
      chl_mg_m3: chl,
      wind_speed_kmh: wind,
      wind_direction_deg: 215.0,
      current_speed_ms: curr,
      current_direction_deg: 112.0,
      wave_height_m: wave,
      wave_period_s: 6.5,
      bsi_score: bsi
    },
    provenance: {
      cached: true,
      sector_key: `lat_${nLat.toFixed(1)}_lon_${nLon.toFixed(1)}`,
      source: 'INCOIS Live Telemetry & Open-Meteo Fallback'
    }
  };
}
