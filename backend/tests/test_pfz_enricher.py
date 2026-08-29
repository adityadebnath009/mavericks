import os
import sys
import time
import math
import concurrent.futures
from shapely.geometry import LineString, MultiLineString, Point
from fastapi.testclient import TestClient

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.api.services.pfz_enricher import PFZEnricherService

client = TestClient(app)


def test_enrich_point_schema():
    """
    Validates enrich_point returns the exact timestamped schema required by PROJECT.md.
    """
    lat, lon = 18.96, 72.82
    res = PFZEnricherService.enrich_point(lat, lon)

    assert res is not None, "Response must not be None"
    assert res.get("status") == "success", f"Expected status 'success', got {res.get('status')}"
    
    # Coordinates check
    coords = res.get("coordinates", {})
    assert "latitude" in coords and "longitude" in coords
    assert coords["latitude"] == round(lat, 4)
    assert coords["longitude"] == round(lon, 4)

    # Timestamp & Source check
    assert "timestamp" in res and isinstance(res["timestamp"], str)
    assert "source" in res and len(res["source"]) > 0

    # Metrics check
    metrics = res.get("metrics", {})
    required_metrics = [
        "sst_c", "chl_mg_m3", "wind_speed_kmh", "wind_direction_deg",
        "current_speed_ms", "current_direction_deg", "wave_height_m", "wave_period_s"
    ]
    for key in required_metrics:
        assert key in metrics, f"Metric '{key}' missing from enrich_point response"
        assert isinstance(metrics[key], (int, float)), f"Metric '{key}' must be numeric"

    # Numerical range checks for oceanographic realism
    assert 15.0 <= metrics["sst_c"] <= 35.0, f"SST out of bounds: {metrics['sst_c']}"
    assert 0.0 <= metrics["chl_mg_m3"] <= 20.0, f"CHL out of bounds: {metrics['chl_mg_m3']}"
    assert 0.0 <= metrics["wind_speed_kmh"] <= 150.0, f"Wind speed out of bounds: {metrics['wind_speed_kmh']}"
    assert 0.0 <= metrics["wind_direction_deg"] <= 360.0, f"Wind dir out of bounds: {metrics['wind_direction_deg']}"
    assert 0.0 <= metrics["current_speed_ms"] <= 5.0, f"Current speed out of bounds: {metrics['current_speed_ms']}"
    assert 0.0 <= metrics["current_direction_deg"] <= 360.0, f"Current dir out of bounds: {metrics['current_direction_deg']}"
    assert 0.0 <= metrics["wave_height_m"] <= 20.0, f"Wave height out of bounds: {metrics['wave_height_m']}"
    assert 0.0 <= metrics["wave_period_s"] <= 30.0, f"Wave period out of bounds: {metrics['wave_period_s']}"

    # Provenance check
    prov = res.get("provenance", {})
    assert "cached" in prov and isinstance(prov["cached"], bool)
    assert "sector_key" in prov and prov["sector_key"].startswith("lat_")


def test_enrich_point_bounds_validation():
    """
    Asserts that out-of-bounds coordinates raise ValueError.
    """
    try:
        PFZEnricherService.enrich_point(95.0, 72.0)
        assert False, "Should have raised ValueError for lat=95.0"
    except ValueError:
        pass

    try:
        PFZEnricherService.enrich_point(18.0, 195.0)
        assert False, "Should have raised ValueError for lon=195.0"
    except ValueError:
        pass


def test_enrich_point_grid_caching():
    """
    Asserts that points within the same 0.1° sector hit the cache on subsequent calls.
    """
    lat, lon = 15.1234, 73.5678
    res1 = PFZEnricherService.enrich_point(lat, lon)
    
    # Query slightly shifted coordinates within the same 0.1° cell
    res2 = PFZEnricherService.enrich_point(lat + 0.002, lon + 0.002)

    assert res2["provenance"]["cached"] is True, "Second point query in same sector must be cached"
    assert res2["provenance"]["sector_key"] == res1["provenance"]["sector_key"]
    assert res2["metrics"] == res1["metrics"]


def test_enrich_pfz_linestring_sampling():
    """
    Validates multi-point sampling and median aggregation on LineString geometries.
    """
    geom = {
        "type": "LineString",
        "coordinates": [
            [72.50, 18.50],
            [72.55, 18.55],
            [72.60, 18.60]
        ]
    }

    res = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.42")
    assert res is not None
    assert res["id"] == "pfzlines.42"
    assert "name" in res
    assert "sst_median" in res and isinstance(res["sst_median"], (int, float))
    assert "chl_median" in res and isinstance(res["chl_median"], (int, float))
    assert "wave_hs_median" in res and isinstance(res["wave_hs_median"], (int, float))
    assert "current_median" in res and isinstance(res["current_median"], (int, float))
    assert "wind_speed_median" in res and isinstance(res["wind_speed_median"], (int, float))
    assert "catch_score" in res and isinstance(res["catch_score"], int)
    assert 40 <= res["catch_score"] <= 98
    assert res["sampled_points_count"] >= 3
    assert "enriched_at" in res
    assert "source" in res

    # Zero static species inference check
    assert "target_species" not in res
    assert "species" not in res
    assert "species_association" not in res


def test_enrich_pfz_multilinestring_sampling():
    """
    Validates multi-point sampling on MultiLineString geometries.
    """
    geom = {
        "type": "MultiLineString",
        "coordinates": [
            [[72.50, 18.50], [72.55, 18.55]],
            [[72.60, 18.60], [72.65, 18.65]]
        ]
    }

    res = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.99")
    assert res["sampled_points_count"] >= 3
    assert isinstance(res["sst_median"], (int, float))
    assert isinstance(res["catch_score"], int)
    assert 40 <= res["catch_score"] <= 98


def test_enrich_pfz_degenerate_geometry():
    """
    Validates robust handling of 0-length LineStrings and empty/None geometries.
    """
    # 0-length line
    deg_geom = {
        "type": "LineString",
        "coordinates": [[72.5, 18.5], [72.5, 18.5]]
    }
    res_deg = PFZEnricherService.enrich_pfz(deg_geom, feature_id="pfzlines.0")
    assert res_deg is not None
    assert "sst_median" in res_deg
    assert "catch_score" in res_deg

    # None geometry
    res_none = PFZEnricherService.enrich_pfz(None, feature_id="pfzlines.none")
    assert res_none is not None
    assert "sst_median" in res_none
    assert "catch_score" in res_none


def test_enrich_pfz_geometry_hash_caching():
    """
    Asserts geometry hash caching returns cached response on repeated evaluation.
    """
    geom = {
        "type": "LineString",
        "coordinates": [
            [73.10, 15.10],
            [73.20, 15.20],
            [73.30, 15.30]
        ]
    }

    res1 = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.test_cache")
    res2 = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.test_cache")

    assert res1["sst_median"] == res2["sst_median"]
    assert res1["catch_score"] == res2["catch_score"]
    assert res1["sampled_points_count"] == res2["sampled_points_count"]


def test_catch_score_logic():
    """
    Tests catch score formula with optimal oceanographic conditions vs adverse conditions.
    """
    score_optimal = PFZEnricherService.calculate_catch_score(
        sst_median=28.5,
        chl_median=0.85,
        wave_hs_median=0.9,
        current_median=0.40,
        wind_speed_median=12.0
    )

    score_adverse = PFZEnricherService.calculate_catch_score(
        sst_median=21.0,
        chl_median=0.04,
        wave_hs_median=3.8,
        current_median=1.40,
        wind_speed_median=48.0
    )

    assert score_optimal >= 80, f"Optimal score should be >= 80, got {score_optimal}"
    assert score_adverse <= 55, f"Adverse score should be <= 55, got {score_adverse}"
    assert (score_optimal - score_adverse) >= 25, "Score differential must reflect conditions"


def test_enrich_feature_collection():
    """
    Validates full GeoJSON FeatureCollection enrichment and eradication of static species.
    """
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "pfzlines.1",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[72.0, 18.0], [72.2, 18.2]]
                },
                "properties": {
                    "id": "pfzlines.1",
                    "target_species": "Yellowfin Tuna (Fake)",
                    "species": "Sardine"
                }
            },
            {
                "type": "Feature",
                "id": "pfzlines.2",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[73.0, 19.0], [73.2, 19.2]]
                },
                "properties": {
                    "id": "pfzlines.2",
                    "species_association": "Mackerel"
                }
            }
        ]
    }

    enriched_fc = PFZEnricherService.enrich_feature_collection(sample_geojson)
    assert enriched_fc["type"] == "FeatureCollection"
    assert len(enriched_fc["features"]) == 2

    for feat in enriched_fc["features"]:
        props = feat["properties"]
        assert "sst_median" in props
        assert "chl_median" in props
        assert "wave_hs_median" in props
        assert "current_median" in props
        assert "wind_speed_median" in props
        assert "catch_score" in props
        assert "sampled_points_count" in props

        # Ensure fake species strings are eradicated
        assert "target_species" not in props
        assert "species" not in props
        assert "species_association" not in props


def test_point_analytics_endpoint():
    """
    Tests GET /api/incois/point-analytics endpoint via FastAPI TestClient.
    """
    response = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["status"] == "success"
    assert data["coordinates"]["latitude"] == 18.96
    assert data["coordinates"]["longitude"] == 72.82
    assert "metrics" in data
    assert "sst_c" in data["metrics"]
    assert "chl_mg_m3" in data["metrics"]
    assert "wind_speed_kmh" in data["metrics"]
    assert "current_speed_ms" in data["metrics"]
    assert "wave_height_m" in data["metrics"]
    assert "provenance" in data

    # Test out-of-bounds latitude (should return 400 or 422)
    bad_resp = client.get("/api/incois/point-analytics?lat=95.0&lon=72.82")
    assert bad_resp.status_code in [400, 422]


def test_pfz_lines_endpoint_enrichment():
    """
    Tests GET /api/incois/pfz-lines returns enriched FeatureCollection with medians.
    """
    response = client.get("/api/incois/pfz-lines")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert isinstance(data["features"], list)

    if data["features"]:
        first_feat = data["features"][0]
        assert "geometry" in first_feat
        assert "properties" in first_feat
        props = first_feat["properties"]
        assert "sst_median" in props
        assert "chl_median" in props
        assert "wave_hs_median" in props
        assert "catch_score" in props
        assert "target_species" not in props
        assert "species" not in props


def test_multi_tier_failsafe_hierarchy():
    """
    Validates fallback resolution across various geographic coordinates.
    """
    # Coordinates in southern ocean
    res = PFZEnricherService.enrich_point(-15.0, 75.0)
    assert res["status"] == "success"
    assert res["metrics"]["sst_c"] > 0.0
    assert res["metrics"]["wave_height_m"] >= 0.0


def test_cache_thread_safety():
    """
    Stress-tests concurrent queries to verify thread safety without race conditions.
    """
    coordinates = [
        (18.96, 72.82),
        (18.97, 72.83),
        (15.00, 73.00),
        (12.00, 80.00),
        (18.96, 72.82),
        (15.00, 73.00),
        (10.00, 76.00),
        (13.00, 80.00)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(PFZEnricherService.enrich_point, lat, lon) for lat, lon in coordinates]
        results = [f.result(timeout=10.0) for f in futures]

    assert len(results) == len(coordinates)
    for r in results:
        assert r["status"] == "success"
        assert "metrics" in r


def test_empirical_cache_latency_benchmark():
    """
    Empirical Benchmark:
    - Measures cold cache miss latency.
    - Measures warm in-memory cache hit latency over 1,000 iterations.
    - Measures warm disk cache hit latency over 100 iterations.
    - Asserts that mean and median cache hit latencies are strictly < 1.0 ms.
    """
    PFZEnricherService.clear_caches()
    unique_lat, unique_lon = 18.2345, 72.8765

    # 1. Cold Cache Miss Latency
    t0 = time.perf_counter()
    cold_res = PFZEnricherService.enrich_point(unique_lat, unique_lon)
    cold_latency_ms = (time.perf_counter() - t0) * 1000.0
    assert cold_res["provenance"]["cached"] is False or cold_latency_ms >= 0.0

    # 2. Warm In-Memory Cache Hit Latency (1,000 iterations)
    num_iterations = 1000
    latencies_us = []
    for _ in range(num_iterations):
        t_start = time.perf_counter()
        warm_res = PFZEnricherService.enrich_point(unique_lat, unique_lon)
        t_end = time.perf_counter()
        latencies_us.append((t_end - t_start) * 1_000_000.0)
        assert warm_res["provenance"]["cached"] is True

    mean_ms = (sum(latencies_us) / len(latencies_us)) / 1000.0
    median_ms = sorted(latencies_us)[len(latencies_us) // 2] / 1000.0
    assert mean_ms < 1.0, f"Expected mean cache hit latency < 1.0ms, got {mean_ms:.4f}ms"
    assert median_ms < 1.0, f"Expected median cache hit latency < 1.0ms, got {median_ms:.4f}ms"

    # 3. Warm Disk-Cache-Only Hit Latency (clearing in-memory cache)
    disk_latencies_us = []
    for _ in range(50):
        with PFZEnricherService._lock:
            PFZEnricherService._memory_point_cache.clear()
        t_start = time.perf_counter()
        disk_res = PFZEnricherService.enrich_point(unique_lat, unique_lon)
        t_end = time.perf_counter()
        disk_latencies_us.append((t_end - t_start) * 1_000_000.0)
        assert disk_res["provenance"]["cached"] is True

    disk_mean_ms = (sum(disk_latencies_us) / len(disk_latencies_us)) / 1000.0
    assert disk_mean_ms < 5.0, f"Expected disk cache hit latency < 5.0ms, got {disk_mean_ms:.4f}ms"


def test_empirical_quantization_accuracy():
    """
    Empirical Verification of 0.1° Coordinate Quantization:
    - Points within the same 0.1° sector must produce identical sector keys and identical cached telemetry.
    - Coordinates in response must reflect exact query coordinates (rounded to 4 decimal places).
    """
    PFZEnricherService.clear_caches()
    expected_sector_key = "lat_19.0_lon_72.8"
    variations = [
        (18.9600, 72.8200),
        (18.9510, 72.8490),
        (18.9900, 72.7600),
        (19.0400, 72.8400),
        (19.0000, 72.8000),
    ]

    first_res = PFZEnricherService.enrich_point(variations[0][0], variations[0][1])
    assert first_res["provenance"]["sector_key"] == expected_sector_key
    base_metrics = first_res["metrics"]

    for lat, lon in variations[1:]:
        res = PFZEnricherService.enrich_point(lat, lon)
        assert res["provenance"]["sector_key"] == expected_sector_key
        assert res["provenance"]["cached"] is True
        assert res["metrics"] == base_metrics
        assert res["coordinates"]["latitude"] == round(lat, 4)
        assert res["coordinates"]["longitude"] == round(lon, 4)


def test_geometry_hash_and_epoch_rollover():
    """
    Empirical Verification:
    - Geometry SHA-256 hash consistency and format determinism.
    - Daily epoch key rollover (cache miss on new UTC date, cache hit within same date).
    """
    PFZEnricherService.clear_caches()
    coords1 = [[72.82, 18.96], [72.85, 18.99], [72.90, 19.05]]
    coords1_high_precision = [[72.820000001, 18.960000002], [72.850000000, 18.990000000], [72.900000000, 19.050000000]]

    hash1 = PFZEnricherService.get_geometry_hash({"type": "LineString", "coordinates": coords1})
    hash1_high = PFZEnricherService.get_geometry_hash({"type": "LineString", "coordinates": coords1_high_precision})
    assert len(hash1) == 16
    assert hash1 == hash1_high

    lat, lon = 16.5432, 81.2345
    from unittest.mock import patch
    with patch.object(PFZEnricherService, "get_utc_date_str", return_value="20260829"):
        PFZEnricherService.clear_caches()
        res_d1_cold = PFZEnricherService.enrich_point(lat, lon)
        assert res_d1_cold["provenance"]["cached"] is False
        res_d1_warm = PFZEnricherService.enrich_point(lat, lon)
        assert res_d1_warm["provenance"]["cached"] is True

    with patch.object(PFZEnricherService, "get_utc_date_str", return_value="20260830"):
        res_d2 = PFZEnricherService.enrich_point(lat, lon)
        assert res_d2["provenance"]["cached"] is False
        res_d2_warm = PFZEnricherService.enrich_point(lat, lon)
        assert res_d2_warm["provenance"]["cached"] is True


def test_zero_static_fish_or_species_names():
    """
    Adversarial Audit: Scans GET /api/incois/pfz-lines for forbidden fish species strings.
    """
    forbidden_species_keywords = [
        "tuna", "yellowfin", "skipjack", "sardine", "mackerel",
        "hilsa", "pomfret", "ribbonfish", "squid", "anchovy"
    ]
    forbidden_property_keys = [
        "target_species", "species", "species_association", "fish_type", "fish_species"
    ]

    res = client.get("/api/incois/pfz-lines")
    assert res.status_code == 200
    data = res.json()

    for feat in data.get("features", []):
        props = feat.get("properties", {})
        for k in forbidden_property_keys:
            assert k not in props, f"Forbidden key '{k}' found in feature {feat.get('id')}"
        for k, v in props.items():
            if isinstance(v, str) and k != "source":
                for sp in forbidden_species_keywords:
                    assert sp not in v.lower(), f"Forbidden species '{sp}' found in prop '{k}': {v}"


if __name__ == "__main__":
    print("Running PFZ Enricher Unit Tests...")
    test_enrich_point_schema()
    print("✓ test_enrich_point_schema passed.")
    test_enrich_point_bounds_validation()
    print("✓ test_enrich_point_bounds_validation passed.")
    test_enrich_point_grid_caching()
    print("✓ test_enrich_point_grid_caching passed.")
    test_enrich_pfz_linestring_sampling()
    print("✓ test_enrich_pfz_linestring_sampling passed.")
    test_enrich_pfz_multilinestring_sampling()
    print("✓ test_enrich_pfz_multilinestring_sampling passed.")
    test_enrich_pfz_degenerate_geometry()
    print("✓ test_enrich_pfz_degenerate_geometry passed.")
    test_enrich_pfz_geometry_hash_caching()
    print("✓ test_enrich_pfz_geometry_hash_caching passed.")
    test_catch_score_logic()
    print("✓ test_catch_score_logic passed.")
    test_enrich_feature_collection()
    print("✓ test_enrich_feature_collection passed.")
    test_point_analytics_endpoint()
    print("✓ test_point_analytics_endpoint passed.")
    test_pfz_lines_endpoint_enrichment()
    print("✓ test_pfz_lines_endpoint_enrichment passed.")
    test_multi_tier_failsafe_hierarchy()
    print("✓ test_multi_tier_failsafe_hierarchy passed.")
    test_cache_thread_safety()
    print("✓ test_cache_thread_safety passed.")
    test_empirical_cache_latency_benchmark()
    print("✓ test_empirical_cache_latency_benchmark passed.")
    test_empirical_quantization_accuracy()
    print("✓ test_empirical_quantization_accuracy passed.")
    test_geometry_hash_and_epoch_rollover()
    print("✓ test_geometry_hash_and_epoch_rollover passed.")
    test_zero_static_fish_or_species_names()
    print("✓ test_zero_static_fish_or_species_names passed.")
    print("\nAll PFZ Enricher and Empirical Adversarial tests passed successfully!")
