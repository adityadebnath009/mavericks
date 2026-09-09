/**
 * @typedef {Object} MapOverlayLayer
 * @property {string} id
 * @property {string} title
 * @property {"raster" | "geojson" | "heatmap"} type
 * @property {"GEE" | "INCOIS" | "ORCA"} provider
 * @property {boolean} visible
 * @property {number} [opacity]
 * @property {string[]} [tiles]
 * @property {Object} [data] - GeoJSON FeatureCollection
 * @property {"AVAILABLE" | "UNAVAILABLE"} [status]
 * @property {Object} [legend]
 */

/**
 * @typedef {Object} Synthesis
 * @property {string} executive_summary
 * @property {Array<{text: string, severity: string}>} identified_hazards
 * @property {Array<{text: string}>} operational_directives
 */

/**
 * @typedef {Object} MapData
 * @property {Object|null} activeRoute
 * @property {Array} pfzPoints
 * @property {Array} geofences
 * @property {MapOverlayLayer[]} overlayLayers
 */

/**
 * @typedef {Object} PipelineResult
 * @property {string} assessment - SAFE | MODERATE | HIGH | EXTREME
 * @property {string} certification - VALID | UNVALIDATED
 * @property {boolean} isSafetyFloorTriggered
 * @property {Synthesis} synthesis
 * @property {number} evidenceMet
 * @property {number} evidenceRequired
 * @property {string[]} sources
 * @property {string[]} ragFootnotes
 * @property {string[]} followups
 * @property {MapData} mapData
 */

// This file serves as the strict type contract between the ORCA Backend Planner Agent and the React Frontend Dumb Renderer.
export {};
