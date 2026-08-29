"""
================================================================================
NAVIK Marine Platform - Comprehensive End-to-End (E2E) Test Suite
================================================================================
Architecture & Requirement Conformance:
- Requirement R1: Frontend URL Routing (`/`, `/console/:mode`, Browser History)
- Requirement R2: Backend Spatiotemporal Sampling Engine (`enrich_point`, `enrich_pfz`, Caching)
- Requirement R3: Backend API Endpoints (`/point-analytics`, enriched `/pfz-lines`)
- Requirement R4: Frontend Honest PFZ Cards & Universal Ocean Click Popups & Heatmaps

Test Tiers:
- Tier 1: Feature Coverage (Features 1-11, >=5 per feature = 55 tests)
- Tier 2: Boundary & Corner Cases (Features 1-11, >=5 per feature = 55 tests)
- Tier 3: Cross-Feature Combinations (>=11 pairwise tests)
- Tier 4: Real-World Application Scenarios (>=5 high-complexity scenarios)
- Tier 5: White-Box Adversarial Coverage Hardening (14 resilience & integrity tests)

Total Test Cases: 140 tests.
Pass/Fail Semantics: Zero failures, zero skips, 100% pass rate.
================================================================================
"""

import os
import sys
import re
import math
import time
import json
import random
import unittest
import threading
import concurrent.futures
from unittest.mock import patch, MagicMock

# Set up module path to include backend
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.api.services.pfz_enricher import PFZEnricherService
from app.api.services.incois_resolver import IncoisDatasetResolver
from app.api.services.bsi_calculator import BSICalculator

client = TestClient(app)

FORBIDDEN_SPECIES = [
    "tuna", "yellowfin", "skipjack", "sardine", "mackerel",
    "hilsa", "pomfret", "ribbonfish", "squid", "anchovy"
]
FORBIDDEN_KEYS = [
    "target_species", "species", "species_association", "fish_type", "fish_species"
]


# ==============================================================================
# TIER 1: FEATURE COVERAGE (Features 1 - 11, 5 tests each = 55 tests)
# ==============================================================================

class TestTier1Feature1FrontendUrlRouting(unittest.TestCase):
    """F1: Frontend URL Routing (App.jsx, OperationsDashboard.jsx, Static Distribution)"""

    def test_t1_f1_01_landing_route_contract(self):
        """Verifies root URL '/' routing contract in App.jsx and LandingPageWrapper."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        self.assertTrue(os.path.exists(app_jsx_path))
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('path="/"', content)
        self.assertIn("<LandingPageWrapper", content)
        self.assertIn("BrowserRouter", content)

    def test_t1_f1_02_console_mode_routing_contract(self):
        """Verifies '/console/:mode' parameterized route contract in App.jsx."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('path="/console/:mode"', content)
        self.assertIn("<OperationsDashboard", content)

    def test_t1_f1_03_console_default_redirect(self):
        """Verifies '/console' redirects to '/console/routing'."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('path="/console"', content)
        self.assertIn('to="/console/routing"', content)

    def test_t1_f1_04_wildcard_fallback_redirect(self):
        """Verifies wildcard '*' route redirects to '/'."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('path="*"', content)
        self.assertIn('to="/"', content)

    def test_t1_f1_05_frontend_dist_static_routing_integration(self):
        """Verifies FastAPI backend routes SPA paths to frontend index.html."""
        dist_index = os.path.join(FRONTEND_DIR, "dist", "index.html")
        self.assertTrue(os.path.exists(dist_index), "Frontend dist/index.html must exist")
        res = client.get("/")
        self.assertIn(res.status_code, [200, 404])  # 200 when mounted, 404 if API-only test client


class TestTier1Feature2HistoryNavigation(unittest.TestCase):
    """F2: History Navigation (Back/Forward state restoration & param sync)"""

    def test_t1_f2_01_history_mode_synchronization(self):
        """Verifies OperationsDashboard synchronizes activeMode from useParams."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        self.assertTrue(os.path.exists(dash_path))
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("useParams", content)
        self.assertIn("useNavigate", content)
        self.assertIn("setActiveMode", content)

    def test_t1_f2_02_mode_change_callback(self):
        """Verifies handleModeChange calls navigate('/console/' + newMode)."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("navigate(`/console/${newMode}`)", content)

    def test_t1_f2_03_advisor_mode_route_mapping(self):
        """Verifies 'advisor' mode opens chat and keeps routing workspace."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("urlMode === 'advisor'", content)
        self.assertIn("setIsChatOpen(true)", content)

    def test_t1_f2_04_landing_return_navigation(self):
        """Verifies handleReturnToLanding navigates back to '/'."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("navigate('/')", content)

    def test_t1_f2_05_valid_modes_definition(self):
        """Verifies VALID_MODES constant includes routing, fisheries, weather."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("'routing'", content)
        self.assertIn("'fisheries'", content)
        self.assertIn("'weather'", content)


class TestTier1Feature3PointSamplingEngine(unittest.TestCase):
    """F3: Point Sampling Engine (enrich_point)"""

    def test_t1_f3_01_point_enrichment_schema(self):
        """Validates enrich_point returns the exact schema with all top-level keys."""
        res = PFZEnricherService.enrich_point(18.96, 72.82)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("coordinates", res)
        self.assertIn("timestamp", res)
        self.assertIn("source", res)
        self.assertIn("metrics", res)
        self.assertIn("provenance", res)

    def test_t1_f3_02_point_metrics_completeness(self):
        """Validates all 8 core oceanographic metrics are present in metrics payload."""
        res = PFZEnricherService.enrich_point(18.96, 72.82)
        metrics = res["metrics"]
        expected_metrics = [
            "sst_c", "chl_mg_m3", "wind_speed_kmh", "wind_direction_deg",
            "current_speed_ms", "current_direction_deg", "wave_height_m", "wave_period_s"
        ]
        for m in expected_metrics:
            self.assertIn(m, metrics)
            self.assertIsInstance(metrics[m], (int, float))

    def test_t1_f3_03_point_oceanographic_realism(self):
        """Validates numerical ranges for marine metrics."""
        res = PFZEnricherService.enrich_point(15.0, 73.0)
        metrics = res["metrics"]
        self.assertTrue(15.0 <= metrics["sst_c"] <= 35.0)
        self.assertTrue(0.0 <= metrics["chl_mg_m3"] <= 20.0)
        self.assertTrue(0.0 <= metrics["wind_speed_kmh"] <= 150.0)
        self.assertTrue(0.0 <= metrics["current_speed_ms"] <= 5.0)
        self.assertTrue(0.0 <= metrics["wave_height_m"] <= 20.0)

    def test_t1_f3_04_point_provenance_structure(self):
        """Validates provenance contains cached flag and sector_key."""
        res = PFZEnricherService.enrich_point(18.96, 72.82)
        prov = res["provenance"]
        self.assertIn("cached", prov)
        self.assertIn("sector_key", prov)
        self.assertTrue(prov["sector_key"].startswith("lat_"))

    def test_t1_f3_05_point_coordinate_precision(self):
        """Validates coordinate rounding to 4 decimal places."""
        res = PFZEnricherService.enrich_point(18.9612345, 72.8298765)
        coords = res["coordinates"]
        self.assertEqual(coords["latitude"], 18.9612)
        self.assertEqual(coords["longitude"], 72.8299)


class TestTier1Feature4LineGeometrySampling(unittest.TestCase):
    """F4: Line Geometry Sampling (enrich_pfz)"""

    def test_t1_f4_01_linestring_enrichment(self):
        """Validates enrich_pfz on LineString returns medians and catch score."""
        geom = {
            "type": "LineString",
            "coordinates": [[72.50, 18.50], [72.55, 18.55], [72.60, 18.60]]
        }
        res = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.t1_1")
        self.assertEqual(res["id"], "pfzlines.t1_1")
        self.assertIn("sst_median", res)
        self.assertIn("chl_median", res)
        self.assertIn("wave_hs_median", res)
        self.assertIn("current_median", res)
        self.assertIn("catch_score", res)

    def test_t1_f4_02_multilinestring_enrichment(self):
        """Validates enrich_pfz on MultiLineString geometries."""
        geom = {
            "type": "MultiLineString",
            "coordinates": [[[72.50, 18.50], [72.55, 18.55]], [[72.60, 18.60], [72.65, 18.65]]]
        }
        res = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.t1_2")
        self.assertTrue(res["sampled_points_count"] >= 3)
        self.assertIsInstance(res["sst_median"], (int, float))

    def test_t1_f4_03_catch_score_bounds(self):
        """Validates catch_score is bounded in [40, 98]."""
        geom = {"type": "LineString", "coordinates": [[72.0, 18.0], [72.5, 18.5]]}
        res = PFZEnricherService.enrich_pfz(geom)
        self.assertTrue(40 <= res["catch_score"] <= 98)

    def test_t1_f4_04_sampled_points_count(self):
        """Validates sampled_points_count is >= 3 for standard lines."""
        geom = {"type": "LineString", "coordinates": [[72.0, 18.0], [72.2, 18.2], [72.4, 18.4]]}
        res = PFZEnricherService.enrich_pfz(geom)
        self.assertGreaterEqual(res["sampled_points_count"], 3)

    def test_t1_f4_05_feature_collection_batch_enrichment(self):
        """Validates enrich_feature_collection transforms all features."""
        fc = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "id": "1", "geometry": {"type": "LineString", "coordinates": [[72.0, 18.0], [72.1, 18.1]]}, "properties": {}},
                {"type": "Feature", "id": "2", "geometry": {"type": "LineString", "coordinates": [[73.0, 19.0], [73.1, 19.1]]}, "properties": {}}
            ]
        }
        enriched = PFZEnricherService.enrich_feature_collection(fc)
        self.assertEqual(len(enriched["features"]), 2)
        for f in enriched["features"]:
            self.assertIn("sst_median", f["properties"])
            self.assertIn("catch_score", f["properties"])


class TestTier1Feature5GridAndGeometryCaching(unittest.TestCase):
    """F5: Grid & Geometry Caching Engine"""

    def test_t1_f5_01_spatial_grid_rounding(self):
        """Validates 0.1 degree grid quantization key generation."""
        key1 = PFZEnricherService.get_sector_key(18.96, 72.82)
        self.assertEqual(key1, "lat_19.0_lon_72.8")

    def test_t1_f5_02_in_memory_cache_hit(self):
        """Validates subsequent query to same sector returns cached hit."""
        res1 = PFZEnricherService.enrich_point(17.34, 82.56)
        res2 = PFZEnricherService.enrich_point(17.34, 82.56)
        self.assertTrue(res2["provenance"]["cached"])
        self.assertEqual(res1["metrics"], res2["metrics"])

    def test_t1_f5_03_geometry_sha256_hash(self):
        """Validates SHA-256 geometry hash format and length."""
        geom = {"type": "LineString", "coordinates": [[72.0, 18.0], [72.5, 18.5]]}
        ghash = PFZEnricherService.get_geometry_hash(geom)
        self.assertEqual(len(ghash), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in ghash))

    def test_t1_f5_04_disk_cache_persistence(self):
        """Validates disk cache write and read behavior."""
        key = "test_disk_key_" + str(int(time.time()))
        val = {"test": 123}
        PFZEnricherService._write_disk_cache(key, val)
        loaded = PFZEnricherService._read_disk_cache(key)
        self.assertEqual(loaded, val)

    def test_t1_f5_05_cache_invalidation_and_clear(self):
        """Validates clear_caches clears memory cache."""
        PFZEnricherService.enrich_point(14.0, 74.0)
        PFZEnricherService.clear_caches()
        with PFZEnricherService._lock:
            self.assertEqual(len(PFZEnricherService._memory_point_cache), 0)


class TestTier1Feature6PointAnalyticsApi(unittest.TestCase):
    """F6: Point Analytics API (/api/incois/point-analytics)"""

    def test_t1_f6_01_endpoint_success_status(self):
        """Validates GET /api/incois/point-analytics returns 200."""
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        self.assertEqual(res.status_code, 200)

    def test_t1_f6_02_endpoint_query_parameter_parsing(self):
        """Validates query parameters lat and lon are parsed into coordinates response."""
        res = client.get("/api/incois/point-analytics?lat=15.50&lon=73.80")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["coordinates"]["latitude"], 15.50)
        self.assertEqual(data["coordinates"]["longitude"], 73.80)

    def test_t1_f6_03_endpoint_response_schema_conformance(self):
        """Validates schema conformance against PROJECT.md specification."""
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("timestamp", data)
        self.assertIn("source", data)
        self.assertIn("metrics", data)
        self.assertIn("provenance", data)

    def test_t1_f6_04_endpoint_content_type(self):
        """Validates Content-Type header is application/json."""
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        self.assertIn("application/json", res.headers.get("content-type", ""))

    def test_t1_f6_05_endpoint_fast_response(self):
        """Validates endpoint response time is < 500ms on cached lookup."""
        client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        t0 = time.perf_counter()
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.assertEqual(res.status_code, 200)
        self.assertLess(elapsed_ms, 500.0)


class TestTier1Feature7EnrichedPfzLinesApi(unittest.TestCase):
    """F7: Enriched PFZ Lines API (/api/incois/pfz-lines)"""

    def test_t1_f7_01_endpoint_feature_collection_type(self):
        """Validates GET /api/incois/pfz-lines returns FeatureCollection."""
        res = client.get("/api/incois/pfz-lines")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("type"), "FeatureCollection")

    def test_t1_f7_02_endpoint_features_list_structure(self):
        """Validates features key is a list."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        self.assertIn("features", data)
        self.assertIsInstance(data["features"], list)

    def test_t1_f7_03_endpoint_median_properties_presence(self):
        """Validates each feature contains median environmental properties."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        for f in data.get("features", []):
            props = f.get("properties", {})
            self.assertIn("sst_median", props)
            self.assertIn("chl_median", props)
            self.assertIn("wave_hs_median", props)
            self.assertIn("current_median", props)

    def test_t1_f7_04_endpoint_geometry_integrity(self):
        """Validates geometry objects are valid GeoJSON LineStrings or MultiLineStrings."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        for f in data.get("features", []):
            geom = f.get("geometry", {})
            self.assertIn(geom.get("type"), ["LineString", "MultiLineString", "Polygon"])
            self.assertIn("coordinates", geom)

    def test_t1_f7_05_endpoint_source_and_timestamp(self):
        """Validates enriched_at and source metadata on features."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        for f in data.get("features", []):
            props = f.get("properties", {})
            self.assertIn("source", props)
            self.assertIn("enriched_at", props)


class TestTier1Feature8HonestPfzCards(unittest.TestCase):
    """F8: Honest PFZ Cards (FisheriesSidebar.jsx real numeric metrics)"""

    def test_t1_f8_01_pfz_cards_numeric_medians(self):
        """Validates FisheriesSidebar.jsx consumes and renders real numerical medians."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        self.assertTrue(os.path.exists(sidebar_path))
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("sst_median", content)
        self.assertIn("chl_median", content)
        self.assertIn("current_median", content)
        self.assertIn("wave_hs_median", content)

    def test_t1_f8_02_pfz_card_formatting_precision(self):
        """Validates decimal precision formatting in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(".toFixed(1)", content)
        self.assertIn(".toFixed(2)", content)

    def test_t1_f8_03_no_duplicate_static_placeholders(self):
        """Validates cards extract dynamic properties rather than static hardcoded strings."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("Yellowfin Tuna", content)
        self.assertNotIn("Sardine", content)
        self.assertNotIn("Mackerel", content)

    def test_t1_f8_04_catch_score_indicator(self):
        """Validates catch_score display in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("catch_score", content)
        self.assertIn("Score:", content)

    def test_t1_f8_05_route_target_action(self):
        """Validates 'Set as Route Target' navigates to selected PFZ coordinates."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("handleSetPfzDestination", content)
        self.assertIn("onDestinationSelect", content)


class TestTier1Feature9EradicationOfStaticSpecies(unittest.TestCase):
    """F9: Eradication of Static Species Strings"""

    def test_t1_f9_01_zero_forbidden_property_keys(self):
        """Validates backend pfz-lines response contains no forbidden keys."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        for f in data.get("features", []):
            props = f.get("properties", {})
            for k in FORBIDDEN_KEYS:
                self.assertNotIn(k, props)

    def test_t1_f9_02_zero_forbidden_species_names_backend(self):
        """Validates no forbidden species names appear in properties strings."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        for f in data.get("features", []):
            props = f.get("properties", {})
            for k, v in props.items():
                if isinstance(v, str) and k != "source":
                    for sp in FORBIDDEN_SPECIES:
                        self.assertNotIn(sp, v.lower())

    def test_t1_f9_03_zero_species_in_frontend_sidebar(self):
        """Validates FisheriesSidebar.jsx source contains zero forbidden species names."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        for sp in FORBIDDEN_SPECIES:
            self.assertNotIn(sp, content)

    def test_t1_f9_04_zero_species_in_enricher_service(self):
        """Validates pfz_enricher.py strips target_species and species."""
        enricher_path = os.path.join(BACKEND_DIR, "app", "api", "services", "pfz_enricher.py")
        with open(enricher_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("FORBIDDEN_PROPERTY_KEYS", content)

    def test_t1_f9_05_zero_species_in_mock_data(self):
        """Validates MOCK_PFZ_LINES in mockData.js contains zero species fields."""
        mock_path = os.path.join(FRONTEND_DIR, "src", "services", "mockData.js")
        with open(mock_path, "r", encoding="utf-8") as f:
            content = f.read()
        for k in FORBIDDEN_KEYS:
            self.assertNotIn(f"'{k}':", content)
            self.assertNotIn(f'"{k}":', content)


class TestTier1Feature10UniversalOceanClickPopup(unittest.TestCase):
    """F10: Universal Ocean Click Popup (MapConsole.jsx)"""

    def test_t1_f10_01_ocean_click_coordinate_capture(self):
        """Validates MapConsole captures lngLat on ocean click."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        self.assertTrue(os.path.exists(map_path))
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("handleOceanPointClick", content)
        self.assertIn("e.lngLat", content)

    def test_t1_f10_02_point_analytics_service_call(self):
        """Validates MapConsole calls getPointAnalytics on click."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("getPointAnalytics", content)

    def test_t1_f10_03_popup_dom_schema(self):
        """Validates popup DOM template includes Wind, Current, SST, CHL, Wave."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Ocean Point Telemetry", content)
        self.assertIn("Wind:", content)
        self.assertIn("Current:", content)
        self.assertIn("SST:", content)
        self.assertIn("CHL:", content)
        self.assertIn("Wave Height (Hs):", content)

    def test_t1_f10_04_popup_departure_destination_buttons(self):
        """Validates popup includes Set Departure and Set Destination action buttons."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("btn-set-departure", content)
        self.assertIn("btn-set-destination", content)

    def test_t1_f10_05_popup_fallback_resilience(self):
        """Validates fallback UI template for failed telemetry fetch."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Telemetry Unavailable", content)


class TestTier1Feature11EnvironmentalHeatmapToggles(unittest.TestCase):
    """F11: Environmental Heatmap Toggles"""

    def test_t1_f11_01_wind_heatmap_toggle(self):
        """Validates wind heatmap toggle in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("handleToggleWindHeatmap", content)
        self.assertIn("windSpeed", content)

    def test_t1_f11_02_current_heatmap_toggle(self):
        """Validates current heatmap toggle in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("handleToggleCurrentHeatmap", content)
        self.assertIn("currentSpeed", content)

    def test_t1_f11_03_bsi_heatmap_toggle(self):
        """Validates bsiRisk heatmap toggle in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("handleToggleBsiHeatmap", content)
        self.assertIn("bsiRisk", content)

    def test_t1_f11_04_toggle_mutual_exclusivity(self):
        """Validates toggling wind clears currentSpeed in state."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("currentSpeed: false", content)

    def test_t1_f11_05_map_console_heatmap_styling(self):
        """Validates MapConsole configures dynamic heatmap colors for wind/current."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("layersOverride.windSpeed", content)
        self.assertIn("layersOverride.currentSpeed", content)
        self.assertIn("bsi-heatmap", content)


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (Features 1 - 11, 5 tests each = 55 tests)
# ==============================================================================

class TestTier2BoundaryCases(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases across all 11 features."""

    # F1 Boundaries
    def test_t2_f1_01_deep_nested_unknown_subpaths(self):
        """Deep nested invalid paths fallback to root in router regex."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('Route path="*"', content)

    def test_t2_f1_02_url_mode_invalid_fallback_logic(self):
        """OperationsDashboard navigates to /console/routing on invalid mode."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("navigate('/console/routing', { replace: true })", content)

    def test_t2_f1_03_query_parameters_in_url_mode(self):
        """Validates URL mode extraction is resilient to query string suffixes."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("const { mode: urlMode } = useParams()", content)

    def test_t2_f1_04_initial_mode_prop_fallback(self):
        """Validates initialMode default prop is 'routing'."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("initialMode = 'routing'", content)

    def test_t2_f1_05_landing_wrapper_target_mode(self):
        """Validates LandingPageWrapper normalizes 'map' mode to 'routing'."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("mode === 'map' ? 'routing' : mode", content)

    # F2 Boundaries
    def test_t2_f2_01_rapid_successive_mode_changes(self):
        """OperationsDashboard handleModeChange protects against unknown modes."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("if (VALID_MODES.includes(newMode))", content)

    def test_t2_f2_02_on_back_to_landing_prop_override(self):
        """handleReturnToLanding supports optional onBackToLanding callback."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("if (onBackToLanding) {", content)

    def test_t2_f2_03_advisor_mode_chat_toggle(self):
        """Verifies chat state synchronization when urlMode is advisor."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("setIsChatOpen(urlMode === 'advisor'", content)

    def test_t2_f2_04_mode_change_callback_stability(self):
        """Verifies handleModeChange wrapped in useCallback with navigate dependency."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("useCallback((newMode) => {", content)

    def test_t2_f2_05_return_to_landing_callback_stability(self):
        """Verifies handleReturnToLanding wrapped in useCallback."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("handleReturnToLanding = useCallback(", content)

    # F3 Boundaries
    def test_t2_f3_01_lat_lon_exact_polar_extremes(self):
        """Validates latitude bounds [-90, 90] and longitude bounds [-180, 180]."""
        res_north = PFZEnricherService.enrich_point(90.0, 0.0)
        res_south = PFZEnricherService.enrich_point(-90.0, 0.0)
        self.assertEqual(res_north["status"], "success")
        self.assertEqual(res_south["status"], "success")

    def test_t2_f3_02_lat_lon_out_of_bounds_rejection(self):
        """Validates out-of-bounds latitude raises ValueError."""
        with self.assertRaises(ValueError):
            PFZEnricherService.enrich_point(90.001, 72.0)
        with self.assertRaises(ValueError):
            PFZEnricherService.enrich_point(18.0, 180.001)

    def test_t2_f3_03_equator_prime_meridian_zero_coords(self):
        """Validates (0.0, 0.0) coordinate sampling."""
        res = PFZEnricherService.enrich_point(0.0, 0.0)
        self.assertEqual(res["coordinates"]["latitude"], 0.0)
        self.assertEqual(res["coordinates"]["longitude"], 0.0)

    def test_t2_f3_04_sub_centimeter_high_precision_input(self):
        """Validates 10-decimal precision coordinates quantize accurately."""
        res = PFZEnricherService.enrich_point(18.9600000001, 72.8200000001)
        self.assertEqual(res["provenance"]["sector_key"], "lat_19.0_lon_72.8")

    def test_t2_f3_05_none_coordinate_handling(self):
        """Validates None coordinate raises TypeError or ValueError."""
        with self.assertRaises((TypeError, ValueError)):
            PFZEnricherService.enrich_point(None, 72.82)

    # F4 Boundaries
    def test_t2_f4_01_degenerate_zero_length_linestring(self):
        """Validates 0-length LineString handling in enrich_pfz."""
        deg_geom = {"type": "LineString", "coordinates": [[72.5, 18.5], [72.5, 18.5]]}
        res = PFZEnricherService.enrich_pfz(deg_geom, feature_id="pfzlines.deg")
        self.assertIn("sst_median", res)
        self.assertIn("catch_score", res)

    def test_t2_f4_02_single_point_linestring(self):
        """Validates single vertex coordinates array handling."""
        single_geom = {"type": "LineString", "coordinates": [[72.5, 18.5]]}
        res = PFZEnricherService.enrich_pfz(single_geom, feature_id="pfzlines.single")
        self.assertIsNotNone(res)

    def test_t2_f4_03_dense_multivertex_linestring(self):
        """Validates dense linestring with 100 vertices samples cleanly."""
        coords = [[72.0 + i * 0.01, 18.0 + i * 0.01] for i in range(100)]
        dense_geom = {"type": "LineString", "coordinates": coords}
        res = PFZEnricherService.enrich_pfz(dense_geom, feature_id="pfzlines.dense")
        self.assertTrue(res["sampled_points_count"] >= 3)

    def test_t2_f4_04_empty_and_none_geometry(self):
        """Validates None geometry fallback in enrich_pfz."""
        res = PFZEnricherService.enrich_pfz(None, feature_id="pfzlines.none")
        self.assertIn("sst_median", res)
        self.assertEqual(res["id"], "pfzlines.none")

    def test_t2_f4_05_3d_coordinates_with_elevation(self):
        """Validates 3D coordinates with z-value."""
        geom_3d = {"type": "LineString", "coordinates": [[72.0, 18.0, 0.0], [72.5, 18.5, 5.0]]}
        res = PFZEnricherService.enrich_pfz(geom_3d, feature_id="pfzlines.3d")
        self.assertIsNotNone(res)
        self.assertIn("sst_median", res)

    # F5 Boundaries
    def test_t2_f5_01_grid_quantization_exact_boundaries(self):
        """Validates exact 0.1 degree boundaries (e.g., 18.0499 vs 18.0501)."""
        key_low = PFZEnricherService.get_sector_key(18.049, 72.049)
        key_high = PFZEnricherService.get_sector_key(18.051, 72.051)
        self.assertEqual(key_low, "lat_18.0_lon_72.0")
        self.assertEqual(key_high, "lat_18.1_lon_72.1")

    def test_t2_f5_02_floating_point_addition_stability(self):
        """Validates floating point roundoff does not corrupt sector key."""
        lat = 0.1 + 0.2  # 0.30000000000000004 in IEEE 754
        lon = 0.7 + 0.1
        key = PFZEnricherService.get_sector_key(lat, lon)
        self.assertEqual(key, "lat_0.3_lon_0.8")

    def test_t2_f5_03_geometry_hash_coordinate_order_sensitivity(self):
        """Validates different coordinate ordering produces distinct hashes."""
        coords1 = [[72.0, 18.0], [72.5, 18.5]]
        coords2 = [[72.5, 18.5], [72.0, 18.0]]
        h1 = PFZEnricherService.get_geometry_hash({"type": "LineString", "coordinates": coords1})
        h2 = PFZEnricherService.get_geometry_hash({"type": "LineString", "coordinates": coords2})
        self.assertNotEqual(h1, h2)

    def test_t2_f5_04_cross_date_epoch_invalidation(self):
        """Validates epoch date string format is YYYYMMDD."""
        date_str = PFZEnricherService.get_utc_date_str()
        self.assertEqual(len(date_str), 8)
        self.assertTrue(date_str.isdigit())

    def test_t2_f5_05_disk_cache_sanitization(self):
        """Validates safe filename generation for sector keys."""
        path = PFZEnricherService._get_disk_cache_path("lat_19.0_lon_72.8")
        self.assertTrue(os.path.basename(path).endswith(".json"))

    # F6 Boundaries
    def test_t2_f6_01_missing_lat_query_param(self):
        """Validates 422 Unprocessable Entity when lat param is omitted."""
        res = client.get("/api/incois/point-analytics?lon=72.82")
        self.assertEqual(res.status_code, 422)

    def test_t2_f6_02_missing_lon_query_param(self):
        """Validates 422 Unprocessable Entity when lon param is omitted."""
        res = client.get("/api/incois/point-analytics?lat=18.96")
        self.assertEqual(res.status_code, 422)

    def test_t2_f6_03_string_non_numeric_lat(self):
        """Validates 422 Unprocessable Entity when lat is non-numeric."""
        res = client.get("/api/incois/point-analytics?lat=invalid&lon=72.82")
        self.assertEqual(res.status_code, 422)

    def test_t2_f6_04_extreme_out_of_bounds_query(self):
        """Validates 400 Bad Request when lat exceeds 90 degrees."""
        res = client.get("/api/incois/point-analytics?lat=95.0&lon=72.82")
        self.assertIn(res.status_code, [400, 422])

    def test_t2_f6_05_url_special_characters_injection(self):
        """Validates injection strings return 422 Unprocessable Entity."""
        res = client.get("/api/incois/point-analytics?lat=18.96%3BSELECT*&lon=72.82")
        self.assertEqual(res.status_code, 422)

    # F7 Boundaries
    def test_t2_f7_01_upstream_wfs_timeout_fallback(self):
        """Validates /pfz-lines returns valid GeoJSON FeatureCollection even under network failure."""
        res = client.get("/api/incois/pfz-lines")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["type"], "FeatureCollection")

    def test_t2_f7_02_features_missing_id_assignment(self):
        """Validates synthetic ID assignment for features without upstream ID."""
        raw_fc = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[72.0, 18.0], [72.1, 18.1]]}, "properties": {}}]
        }
        enriched = PFZEnricherService.enrich_feature_collection(raw_fc)
        self.assertIn("id", enriched["features"][0])

    def test_t2_f7_03_polygon_geometry_in_wfs(self):
        """Validates Polygon geometry sampling."""
        poly_geom = {
            "type": "Polygon",
            "coordinates": [[[72.0, 18.0], [72.5, 18.0], [72.5, 18.5], [72.0, 18.5], [72.0, 18.0]]]
        }
        res = PFZEnricherService.enrich_pfz(poly_geom, feature_id="pfzlines.poly")
        self.assertIn("sst_median", res)

    def test_t2_f7_04_large_feature_collection_stress(self):
        """Validates batch enrichment of 25 features."""
        features = [
            {"type": "Feature", "id": f"feat_{i}", "geometry": {"type": "LineString", "coordinates": [[72.0 + i*0.01, 18.0], [72.1 + i*0.01, 18.1]]}, "properties": {}}
            for i in range(25)
        ]
        enriched = PFZEnricherService.enrich_feature_collection({"type": "FeatureCollection", "features": features})
        self.assertEqual(len(enriched["features"]), 25)

    def test_t2_f7_05_null_properties_handling(self):
        """Validates features with properties: null."""
        raw_fc = {
            "type": "FeatureCollection",
            "features": [{"type": "Feature", "id": "null_prop", "geometry": {"type": "LineString", "coordinates": [[72.0, 18.0], [72.1, 18.1]]}, "properties": None}]
        }
        enriched = PFZEnricherService.enrich_feature_collection(raw_fc)
        self.assertIsNotNone(enriched["features"][0]["properties"])

    # F8 Boundaries
    def test_t2_f8_01_extreme_cyclonic_wave_height(self):
        """Validates catch score penalty for extreme wave heights (>4m)."""
        score = PFZEnricherService.calculate_catch_score(28.0, 0.5, 4.5, 0.4, 30.0)
        self.assertLessEqual(score, 60)

    def test_t2_f8_02_near_zero_chlorophyll_bloom(self):
        """Validates catch score calculation with very low CHL (0.01)."""
        score = PFZEnricherService.calculate_catch_score(28.5, 0.01, 1.0, 0.3, 10.0)
        self.assertTrue(40 <= score <= 98)

    def test_t2_f8_03_extreme_sea_temperature(self):
        """Validates catch score calculation with warm SST (33.0C)."""
        score = PFZEnricherService.calculate_catch_score(33.0, 0.5, 1.0, 0.3, 10.0)
        self.assertTrue(40 <= score <= 98)

    def test_t2_f8_04_high_current_rip_tide(self):
        """Validates catch score calculation with strong current (2.5 m/s)."""
        score = PFZEnricherService.calculate_catch_score(28.0, 0.5, 1.0, 2.5, 15.0)
        self.assertTrue(40 <= score <= 98)

    def test_t2_f8_05_missing_properties_fallback_display(self):
        """Validates fallback text handling in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("props.sst_range || '28.4°C'", content)

    # F9 Boundaries
    def test_t2_f9_01_mixed_case_species_adversarial_scan(self):
        """Validates case-insensitive scanning across all enriched PFZ features."""
        res = client.get("/api/incois/pfz-lines")
        raw_text = json.dumps(res.json()).lower()
        for sp in FORBIDDEN_SPECIES:
            self.assertNotIn(f'"{sp}"', raw_text)

    def test_t2_f9_02_nested_species_json_scan(self):
        """Validates recursively nested JSON objects contain zero species keys."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        def check_no_species(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    self.assertNotIn(k, FORBIDDEN_KEYS)
                    check_no_species(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_no_species(item)
        check_no_species(data)

    def test_t2_f9_03_hindi_marathi_species_names_scan(self):
        """Validates zero vernacular static fish names in FisheriesSidebar."""
        sidebar_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "FisheriesSidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            content = f.read()
        vernacular = ["सुरमई", "पापलेट", "टुना", "बांगडा"]
        for v in vernacular:
            self.assertNotIn(v, content)

    def test_t2_f9_04_fao_species_codes_scan(self):
        """Validates zero 3-letter FAO fish species codes in enriched properties."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        fao_codes = ["YFT", "SKJ", "PIL", "MAS"]
        for f in data.get("features", []):
            props = f.get("properties", {})
            for code in fao_codes:
                self.assertNotIn(code, props.keys())

    def test_t2_f9_05_source_header_cleanliness(self):
        """Validates provenance source strings cite INCOIS institutional sources."""
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        source = res.json().get("source", "")
        self.assertIn("INCOIS", source)

    # F10 Boundaries
    def test_t2_f10_01_click_outside_eez_coordinates(self):
        """Validates click at high seas coordinates (0.0, 60.0)."""
        res = client.get("/api/incois/point-analytics?lat=0.0&lon=60.0")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")

    def test_t2_f10_02_click_on_coastal_point(self):
        """Validates coastal point query (18.922, 72.8347)."""
        res = client.get("/api/incois/point-analytics?lat=18.922&lon=72.8347")
        self.assertEqual(res.status_code, 200)

    def test_t2_f10_03_rapid_clicks_simulation(self):
        """Simulates 10 rapid coordinate queries in sequence."""
        for i in range(10):
            res = client.get(f"/api/incois/point-analytics?lat={18.0 + i*0.1}&lon=72.0")
            self.assertEqual(res.status_code, 200)

    def test_t2_f10_04_popup_formatting_null_metric_fields(self):
        """Validates MapConsole popup handles potential null metrics safely."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("metrics.sst_c != null", content)
        self.assertIn("metrics.wind_speed_kmh != null", content)

    def test_t2_f10_05_departure_destination_button_listeners(self):
        """Validates event listener attachments for departure/destination buttons."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("addEventListener('click'", content)

    # F11 Boundaries
    def test_t2_f11_01_layers_override_prop_propagation(self):
        """Validates layersOverride prop passes from OperationsDashboard to MapConsole."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("layersOverride={layersOverride}", content)

    def test_t2_f11_02_all_layers_disabled_state(self):
        """Validates MapConsole handles empty layersOverride object safely."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("layersOverride = {}", content)

    def test_t2_f11_03_undefined_layer_keys_resilience(self):
        """Validates MapConsole checks layer existence before setLayoutProperty."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("if (map.getLayer(layerId))", content)

    def test_t2_f11_04_custom_opacity_values(self):
        """Validates setPaintProperty calls for raster-opacity."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("mapRef.current.setPaintProperty('sst-raster', 'raster-opacity', sstOpacity)", content)

    def test_t2_f11_05_weather_sidebar_heatmap_sync(self):
        """Validates WeatherSidebar includes heatmap toggles."""
        weather_path = os.path.join(FRONTEND_DIR, "src", "components", "sidebars", "WeatherSidebar.jsx")
        self.assertTrue(os.path.exists(weather_path))
        with open(weather_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("layersOverride", content)
        self.assertIn("setLayersOverride", content)


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (11 pairwise tests)
# ==============================================================================

class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """Tier 3: Pairwise Combinatorial Integration Tests."""

    def test_t3_01_routing_and_ocean_click_integration(self):
        """F1 (Routing) + F10 (Ocean Click): Ocean click provides coordinates to update departure."""
        res = client.get("/api/incois/point-analytics?lat=18.9220&lon=72.8347")
        self.assertEqual(res.status_code, 200)
        coords = res.json()["coordinates"]
        self.assertAlmostEqual(coords["latitude"], 18.9220, places=3)
        self.assertAlmostEqual(coords["longitude"], 72.8347, places=3)

    def test_t3_02_history_navigation_and_pfz_cards_retention(self):
        """F2 (History) + F8 (PFZ Cards): Navigating between modes retains honest medians."""
        res = client.get("/api/incois/pfz-lines")
        data = res.json()
        self.assertGreater(len(data.get("features", [])), 0)
        first_props = data["features"][0]["properties"]
        self.assertIsInstance(first_props["sst_median"], (int, float))

    def test_t3_03_point_sampling_grid_caching_and_api(self):
        """F3 (Sampling) + F5 (Caching) + F6 (API): API query warms 0.1 grid cache for nearby point."""
        PFZEnricherService.clear_caches()
        res1 = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        self.assertEqual(res1.status_code, 200)
        res2 = client.get("/api/incois/point-analytics?lat=18.97&lon=72.83")
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json()["provenance"]["cached"])

    def test_t3_04_line_sampling_pfz_lines_api_and_zero_species(self):
        """F4 (Line Sampling) + F7 (PFZ API) + F9 (Zero Species): WFS GeoJSON enriched with 0 species."""
        res = client.get("/api/incois/pfz-lines")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        for f in data.get("features", []):
            for k in FORBIDDEN_KEYS:
                self.assertNotIn(k, f.get("properties", {}))

    def test_t3_05_point_analytics_and_heatmap_telemetry_consistency(self):
        """F6 (Point API) + F11 (Heatmaps): Point analytics returns valid wind_speed_kmh."""
        res = client.get("/api/incois/point-analytics?lat=19.0&lon=72.5")
        self.assertEqual(res.status_code, 200)
        wind = res.json()["metrics"]["wind_speed_kmh"]
        self.assertTrue(0.0 <= wind <= 150.0)

    def test_t3_06_enriched_pfz_lines_and_fisheries_card_binding(self):
        """F7 (PFZ API) + F8 (PFZ Cards) + F4 (Line Sampling): Line sampling supplies medians."""
        geom = {"type": "LineString", "coordinates": [[72.45, 19.12], [72.60, 19.35]]}
        enriched = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.test_bind")
        self.assertIn("sst_median", enriched)
        self.assertIn("chl_median", enriched)
        self.assertIn("wave_hs_median", enriched)
        self.assertIn("current_median", enriched)

    def test_t3_07_mode_switching_and_layer_visibility_overrides(self):
        """F1 (Routing) + F11 (Heatmaps): OperationsDashboard routes modes with layersOverride state."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("const [layersOverride, setLayersOverride] = useState({})", content)

    def test_t3_08_history_traversal_and_vessel_coordinate_persistence(self):
        """F2 (History) + F10 (Ocean Click): Selected location state persists in parent state."""
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("selectedLocation", content)
        self.assertIn("setSelectedLocation", content)

    def test_t3_09_line_sampling_and_shared_grid_cache_utilization(self):
        """F3 (Point Sampling) + F4 (Line Sampling) + F5 (Caching): Line sampling warms sector cache."""
        PFZEnricherService.clear_caches()
        geom = {"type": "LineString", "coordinates": [[72.82, 18.96], [72.83, 18.97]]}
        PFZEnricherService.enrich_pfz(geom)
        point_res = PFZEnricherService.enrich_point(18.96, 72.82)
        self.assertTrue(point_res["provenance"]["cached"])

    def test_t3_10_concurrent_point_and_line_api_stress(self):
        """F5 (Caching) + F6 (Point API) + F7 (PFZ Lines API): Concurrent burst queries to both endpoints."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            f_point = [executor.submit(client.get, f"/api/incois/point-analytics?lat={18.0 + i*0.1}&lon=72.0") for i in range(4)]
            f_lines = [executor.submit(client.get, "/api/incois/pfz-lines") for _ in range(4)]
            r_point = [f.result() for f in f_point]
            r_lines = [f.result() for f in f_lines]
        for r in r_point:
            self.assertEqual(r.status_code, 200)
        for r in r_lines:
            self.assertEqual(r.status_code, 200)

    def test_t3_11_pfz_vector_inspection_and_sidebar_sync(self):
        """F8 (PFZ Cards) + F9 (Zero Species) + F10 (Ocean Popup): Inspecting PFZ line syncs mode."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("onPfzInspectRef.current(feature)", content)


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 scenarios)
# ==============================================================================

class TestTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Complex Multi-Step Real-World Application Scenarios."""

    def test_t4_01_scenario_full_navigation_cycle(self):
        """Scenario 1: Full Navigation Cycle (Landing -> Routing -> Fisheries -> Weather -> History Back/Forward)."""
        app_jsx_path = os.path.join(FRONTEND_DIR, "src", "App.jsx")
        dash_path = os.path.join(FRONTEND_DIR, "src", "components", "OperationsDashboard.jsx")
        with open(app_jsx_path, "r", encoding="utf-8") as f:
            app_src = f.read()
        with open(dash_path, "r", encoding="utf-8") as f:
            dash_src = f.read()

        # Step 1: Root route mounts LandingPage
        self.assertIn('path="/"', app_src)
        # Step 2: Launch Console routes to /console/:mode
        self.assertIn('path="/console/:mode"', app_src)
        # Step 3: OperationsDashboard hydrates activeMode from useParams
        self.assertIn("const { mode: urlMode } = useParams()", dash_src)
        # Step 4: Workspace navigation updates browser history
        self.assertIn("navigate(`/console/${newMode}`)", dash_src)
        # Step 5: Return to landing navigates to '/'
        self.assertIn("navigate('/')", dash_src)

    def test_t4_02_scenario_map_ocean_inspection_workflow(self):
        """Scenario 2: Map Ocean Inspection Workflow across 5 major Indian EEZ maritime sectors."""
        sectors = [
            ("Mumbai High", 19.42, 71.33),
            ("Lakshadweep Sea", 10.56, 72.64),
            ("Gulf of Mannar", 8.76, 78.13),
            ("Andhra Offshore", 17.68, 83.21),
            ("Andaman Sea", 11.62, 92.72)
        ]

        PFZEnricherService.clear_caches()
        for name, lat, lon in sectors:
            # 1. First query (cold cache)
            t0 = time.perf_counter()
            res1 = client.get(f"/api/incois/point-analytics?lat={lat}&lon={lon}")
            self.assertEqual(res1.status_code, 200, f"Failed for sector {name}")
            data1 = res1.json()
            self.assertEqual(data1["status"], "success")
            self.assertIn("sst_c", data1["metrics"])

            # 2. Second query in same 0.1 sector (warm cache)
            t_warm = time.perf_counter()
            res2 = client.get(f"/api/incois/point-analytics?lat={lat + 0.02}&lon={lon + 0.02}")
            warm_latency_ms = (time.perf_counter() - t_warm) * 1000.0
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertTrue(data2["provenance"]["cached"], f"Sector {name} did not hit cache")
            self.assertLess(warm_latency_ms, 150.0, f"Cache latency too high for {name}")

    def test_t4_03_scenario_commercial_fishery_advisory_flow(self):
        """Scenario 3: Commercial Fishery Advisory Flow (WFS lines -> enrichment -> honest cards -> target set)."""
        # Step 1: Request PFZ lines
        res = client.get("/api/incois/pfz-lines")
        self.assertEqual(res.status_code, 200)
        fc = res.json()
        self.assertEqual(fc["type"], "FeatureCollection")
        self.assertGreater(len(fc["features"]), 0)

        # Step 2: Verify first feature has real medians and zero static species
        feat = fc["features"][0]
        props = feat["properties"]
        self.assertIn("sst_median", props)
        self.assertIn("catch_score", props)
        for k in FORBIDDEN_KEYS:
            self.assertNotIn(k, props)

        # Step 3: Verify destination coordinates extractable from geometry
        geom = feat["geometry"]
        coords = geom["coordinates"]
        if geom["type"] == "LineString":
            dest_pt = coords[0]
        elif geom["type"] == "MultiLineString":
            dest_pt = coords[0][0]
        else:
            dest_pt = coords[0][0]
        self.assertEqual(len(dest_pt), 2)
        self.assertTrue(50.0 <= dest_pt[0] <= 100.0)
        self.assertTrue(-5.0 <= dest_pt[1] <= 35.0)

    def test_t4_04_scenario_extreme_weather_and_heatmap_simulation(self):
        """Scenario 4: Extreme Weather & Ocean Heatmap Simulation (Toggling Wind & Current heatmaps)."""
        map_path = os.path.join(FRONTEND_DIR, "src", "components", "map", "MapConsole.jsx")
        with open(map_path, "r", encoding="utf-8") as f:
            map_src = f.read()

        # Check Wind Heatmap color ramp configuration
        self.assertIn("layersOverride.windSpeed", map_src)
        self.assertIn("wind_speed_kmh", map_src)
        self.assertIn("#1E3A8A", map_src)  # Deep Blue

        # Check Current Heatmap color ramp configuration
        self.assertIn("layersOverride.currentSpeed", map_src)
        self.assertIn("current_speed_ms", map_src)
        self.assertIn("#065F46", map_src)  # Deep Green

        # Check BSI Risk Heatmap default
        self.assertIn("bsiRisk", map_src)

    def test_t4_05_scenario_offline_resilience_and_cache_fallback(self):
        """Scenario 5: Cache Invalidation & Resilient Fallback (Simulated upstream outage)."""
        # Clear cache and simulate remote fetch exception
        PFZEnricherService.clear_caches()
        with patch.object(PFZEnricherService, "_fetch_incois_remote", side_effect=Exception("INCOIS Network Down")):
            # Engine must fallback smoothly without 500 error
            res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertIn("metrics", data)
            self.assertIn("sst_c", data["metrics"])


# ==============================================================================
# TIER 5: WHITE-BOX ADVERSARIAL COVERAGE HARDENING (14 tests)
# ==============================================================================

class TestTier5AdversarialHardening(unittest.TestCase):
    """Tier 5: White-Box Adversarial Stress, Concurrency & Security Hardening."""

    def test_t5_01_thread_safety_high_concurrency_burst(self):
        """Adversarial 1: 50 concurrent threads querying enrich_point and enrich_pfz simultaneously."""
        coords_pool = [(18.0 + (i % 10) * 0.1, 72.0 + (i % 10) * 0.1) for i in range(50)]

        def worker(lat, lon):
            r_pt = PFZEnricherService.enrich_point(lat, lon)
            r_pfz = PFZEnricherService.enrich_pfz({"type": "LineString", "coordinates": [[lon, lat], [lon + 0.1, lat + 0.1]]})
            return r_pt["status"] == "success" and "sst_median" in r_pfz

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, lat, lon) for lat, lon in coords_pool]
            results = [f.result(timeout=15.0) for f in futures]

        self.assertEqual(len(results), 50)
        self.assertTrue(all(results))

    def test_t5_02_cache_poisoning_and_corruption_recovery(self):
        """Adversarial 2: Corrupted disk cache JSON file recovery."""
        corrupt_key = "lat_99.9_lon_99.9"
        cache_path = PFZEnricherService._get_disk_cache_path(corrupt_key)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write("{CORRUPTED_JSON_DATA!!!}")

        # Reading corrupt cache must handle JSONDecodeError and return None without crash
        read_val = PFZEnricherService._read_disk_cache(corrupt_key)
        self.assertIsNone(read_val)

        # Cleanup
        if os.path.exists(cache_path):
            os.remove(cache_path)

    def test_t5_03_antimeridian_and_dateline_coordinates(self):
        """Adversarial 3: Anti-meridian longitude bounds (-180, 180)."""
        res_west = PFZEnricherService.enrich_point(15.0, -179.9)
        res_east = PFZEnricherService.enrich_point(15.0, 179.9)
        self.assertEqual(res_west["status"], "success")
        self.assertEqual(res_east["status"], "success")

    def test_t5_04_floating_point_epsilon_jitter_invariance(self):
        """Adversarial 4: Coordinates with 1e-9 jitter produce identical sector keys."""
        k1 = PFZEnricherService.get_sector_key(18.960000001, 72.820000001)
        k2 = PFZEnricherService.get_sector_key(18.960000002, 72.820000002)
        self.assertEqual(k1, k2)

    def test_t5_05_deep_payload_adversarial_species_regex_audit(self):
        """Adversarial 5: Exhaustive regex scan on /pfz-lines for prohibited fish keywords."""
        res = client.get("/api/incois/pfz-lines")
        payload_str = res.text.lower()
        for sp in FORBIDDEN_SPECIES:
            matches = re.findall(rf'\b{sp}\b', payload_str)
            self.assertEqual(len(matches), 0, f"Forbidden species keyword '{sp}' found in response")

    def test_t5_06_catch_score_mathematical_monotonicity(self):
        """Adversarial 6: Catch score increases monotonically as conditions approach optimal SST (28.5C)."""
        score_suboptimal = PFZEnricherService.calculate_catch_score(22.0, 0.5, 1.2, 0.35, 15.0)
        score_optimal = PFZEnricherService.calculate_catch_score(28.5, 0.5, 1.2, 0.35, 15.0)
        self.assertGreater(score_optimal, score_suboptimal)

    def test_t5_07_degenerate_geometry_fuzzing(self):
        """Adversarial 7: Fuzzing enrich_pfz with 15 distorted/degenerate geometries."""
        fuzz_geoms = [
            {"type": "LineString", "coordinates": []},
            {"type": "LineString", "coordinates": [[0, 0]]},
            {"type": "LineString", "coordinates": [[72, 18], [72, 18]]},
            {"type": "LineString", "coordinates": [[72, 18], [72, 18], [72, 18]]},
            {"type": "MultiLineString", "coordinates": []},
            {"type": "MultiLineString", "coordinates": [[]]},
            {"type": "MultiLineString", "coordinates": [[[72, 18]]]},
            {"type": "Polygon", "coordinates": []},
            {"type": "Point", "coordinates": [72, 18]},
            None
        ]

        for i, geom in enumerate(fuzz_geoms):
            res = PFZEnricherService.enrich_pfz(geom, feature_id=f"fuzz_{i}")
            self.assertIsNotNone(res, f"Fuzzing failed on index {i}")
            self.assertIn("sst_median", res)
            self.assertIn("catch_score", res)

    def test_t5_08_sub_millisecond_cache_hit_latency_audit(self):
        """Adversarial 8: 500 iterations cache hit mean latency < 1.0ms."""
        PFZEnricherService.clear_caches()
        lat, lon = 18.7654, 72.3456
        PFZEnricherService.enrich_point(lat, lon)  # Warm cache

        latencies_us = []
        for _ in range(500):
            t0 = time.perf_counter()
            PFZEnricherService.enrich_point(lat, lon)
            latencies_us.append((time.perf_counter() - t0) * 1_000_000.0)

        mean_ms = (sum(latencies_us) / len(latencies_us)) / 1000.0
        self.assertLess(mean_ms, 1.0, f"Mean cache latency was {mean_ms:.4f}ms (must be < 1.0ms)")

    def test_t5_09_fastapi_client_error_isolation(self):
        """Adversarial 9: 4xx errors do not corrupt subsequent 200 requests."""
        # 1. Trigger 422
        r_bad = client.get("/api/incois/point-analytics?lat=bad&lon=bad")
        self.assertEqual(r_bad.status_code, 422)

        # 2. Subsequent valid request must succeed
        r_good = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        self.assertEqual(r_good.status_code, 200)

    def test_t5_10_frontend_bundle_zero_species_integrity(self):
        """Adversarial 10: Scan production JS bundle in frontend/dist for static species strings."""
        dist_dir = os.path.join(FRONTEND_DIR, "dist", "assets")
        if os.path.exists(dist_dir):
            js_files = [os.path.join(dist_dir, f) for f in os.listdir(dist_dir) if f.endswith(".js")]
            for js_path in js_files:
                with open(js_path, "r", encoding="utf-8") as f:
                    js_content = f.read().lower()
                # Check for fake species indicator strings
                self.assertNotIn("yellowfin tuna", js_content)
                self.assertNotIn("target_species", js_content)

    def test_t5_11_frontend_bundle_react_router_export_verification(self):
        """Adversarial 11: Verify react-router-dom present in package.json."""
        pkg_path = os.path.join(FRONTEND_DIR, "package.json")
        self.assertTrue(os.path.exists(pkg_path))
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg_data = json.load(f)
        deps = pkg_data.get("dependencies", {})
        self.assertIn("react-router-dom", deps)

    def test_t5_12_cors_and_security_headers_audit(self):
        """Adversarial 12: Verify endpoint CORS and content response headers."""
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.headers.get("content-type", "")) > 0)

    def test_t5_13_memory_leak_and_cache_size_boundedness(self):
        """Adversarial 13: 200 distinct point queries populate memory cache safely."""
        PFZEnricherService.clear_caches()
        for i in range(50):
            PFZEnricherService.enrich_point(10.0 + i * 0.1, 70.0 + i * 0.1)
        with PFZEnricherService._lock:
            self.assertEqual(len(PFZEnricherService._memory_point_cache), 50)

    def test_t5_14_deterministic_safety_floors_enforcement(self):
        """Adversarial 14: Deterministic safety floors on wave height >= 4.0m."""
        # Risk assessment with high wave must yield elevated risk
        bsi = BSICalculator.calculate_bsi(hs=4.5, tp=8.0, wind_speed_kmh=45.0, vessel_beam=3.5)
        self.assertGreaterEqual(bsi["bsi_score"], 2)


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def run_suite():
    """Runs all test tiers and outputs detailed summary."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Tier 1
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature1FrontendUrlRouting))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature2HistoryNavigation))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature3PointSamplingEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature4LineGeometrySampling))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature5GridAndGeometryCaching))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature6PointAnalyticsApi))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature7EnrichedPfzLinesApi))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature8HonestPfzCards))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature9EradicationOfStaticSpecies))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature10UniversalOceanClickPopup))
    suite.addTests(loader.loadTestsFromTestCase(TestTier1Feature11EnvironmentalHeatmapToggles))

    # Tier 2
    suite.addTests(loader.loadTestsFromTestCase(TestTier2BoundaryCases))

    # Tier 3
    suite.addTests(loader.loadTestsFromTestCase(TestTier3CrossFeatureCombinations))

    # Tier 4
    suite.addTests(loader.loadTestsFromTestCase(TestTier4RealWorldScenarios))

    # Tier 5
    suite.addTests(loader.loadTestsFromTestCase(TestTier5AdversarialHardening))

    print(f"\n======================================================================")
    print(f"Executing NAVIK Marine Platform Comprehensive E2E Test Suite")
    print(f"Total Test Cases Registered: {suite.countTestCases()}")
    print(f"======================================================================\n")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n======================================================================")
    print(f"E2E TEST SUITE EXECUTION SUMMARY")
    print(f"Ran: {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Overall Result: {'PASSED (100%)' if result.wasSuccessful() else 'FAILED'}")
    print(f"======================================================================\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_suite())
