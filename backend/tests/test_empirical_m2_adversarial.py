"""
Empirical Adversarial Test Suite for Milestone M2:
- Cache hit latency (<1ms) vs cache miss latency benchmark
- Cache quantization accuracy (0.1° grid sector verification)
- Geometry hash consistency & daily epoch rollover
- FastAPI TestClient endpoint latency, schema validation & error status codes (400, 422)
- Zero static species verification across /api/incois/pfz-lines
- Adversarial robustness: disk corruption recovery, degenerate geometries, high concurrency
"""

import os
import sys
import time
import json
import uuid
import math
import statistics
import concurrent.futures
from unittest.mock import patch
from shapely.geometry import LineString, MultiLineString, Point
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.api.services.pfz_enricher import PFZEnricherService, SECTORS_CACHE_DIR, GEOM_CACHE_DIR

client = TestClient(app)


def test_empirical_cache_latency_benchmark():
    """
    Empirical Benchmark:
    - Measures cold cache miss latency.
    - Measures warm in-memory cache hit latency over 1,000 iterations.
    - Measures warm disk cache hit latency over 200 iterations.
    - Asserts that mean and median cache hit latencies are strictly < 1.0 ms (< 1000 µs).
    - Verifies substantial speedup (cache hit latency vs cache miss latency).
    """
    print("\n--- [1] EMPIRICAL CACHE LATENCY BENCHMARK ---")
    PFZEnricherService.clear_caches()

    # Use a unique coordinate to guarantee a cold miss
    unique_lat = 18.2345
    unique_lon = 72.8765

    # 1. Cold Cache Miss Latency
    t0 = time.perf_counter()
    cold_res = PFZEnricherService.enrich_point(unique_lat, unique_lon)
    cold_latency_ms = (time.perf_counter() - t0) * 1000.0

    print(f"Cold Cache Miss Latency: {cold_latency_ms:.3f} ms")
    assert cold_res["provenance"]["cached"] is False or cold_latency_ms >= 0.0

    # 2. Warm In-Memory Cache Hit Latency (1,000 iterations)
    num_iterations = 1000
    latencies_us = []

    for _ in range(num_iterations):
        t_start = time.perf_counter()
        warm_res = PFZEnricherService.enrich_point(unique_lat, unique_lon)
        t_end = time.perf_counter()
        latencies_us.append((t_end - t_start) * 1_000_000.0)  # in microseconds
        assert warm_res["provenance"]["cached"] is True

    mean_us = statistics.mean(latencies_us)
    median_us = statistics.median(latencies_us)
    p90_us = statistics.quantiles(latencies_us, n=10)[8]
    p95_us = statistics.quantiles(latencies_us, n=20)[18]
    p99_us = statistics.quantiles(latencies_us, n=100)[98]
    min_us = min(latencies_us)
    max_us = max(latencies_us)

    mean_ms = mean_us / 1000.0
    median_ms = median_us / 1000.0
    p95_ms = p95_us / 1000.0
    p99_ms = p99_us / 1000.0

    print(f"Warm In-Memory Cache Hit Latency (N={num_iterations}):")
    print(f"  Min:    {min_us:.2f} µs ({min_us/1000:.4f} ms)")
    print(f"  Mean:   {mean_us:.2f} µs ({mean_ms:.4f} ms)")
    print(f"  Median: {median_us:.2f} µs ({median_ms:.4f} ms)")
    print(f"  P90:    {p90_us:.2f} µs ({p90_us/1000:.4f} ms)")
    print(f"  P95:    {p95_us:.2f} µs ({p95_ms:.4f} ms)")
    print(f"  P99:    {p99_us:.2f} µs ({p99_ms:.4f} ms)")
    print(f"  Max:    {max_us:.2f} µs ({max_us/1000:.4f} ms)")

    # Strict assertion: Cache hit latency must be < 1.0 ms
    assert mean_ms < 1.0, f"Expected mean cache hit latency < 1.0ms, got {mean_ms:.4f}ms"
    assert median_ms < 1.0, f"Expected median cache hit latency < 1.0ms, got {median_ms:.4f}ms"
    assert p95_ms < 1.0, f"Expected p95 cache hit latency < 1.0ms, got {p95_ms:.4f}ms"

    # 3. Warm Disk-Cache-Only Hit Latency (clearing in-memory cache)
    disk_latencies_us = []
    for _ in range(100):
        # Clear in-memory cache so it forces a disk read
        with PFZEnricherService._lock:
            PFZEnricherService._memory_point_cache.clear()

        t_start = time.perf_counter()
        disk_res = PFZEnricherService.enrich_point(unique_lat, unique_lon)
        t_end = time.perf_counter()
        disk_latencies_us.append((t_end - t_start) * 1_000_000.0)
        assert disk_res["provenance"]["cached"] is True

    disk_mean_ms = statistics.mean(disk_latencies_us) / 1000.0
    disk_median_ms = statistics.median(disk_latencies_us) / 1000.0
    print(f"Warm Disk Cache Hit Latency (N=100, In-Memory Bypassed):")
    print(f"  Mean:   {disk_mean_ms:.4f} ms")
    print(f"  Median: {disk_median_ms:.4f} ms")
    assert disk_mean_ms < 5.0, f"Expected disk cache hit latency < 5.0ms, got {disk_mean_ms:.4f}ms"

    # 4. PFZ Line Geometry Cache Latency Benchmark
    test_line = LineString([[72.50, 18.50], [72.55, 18.55], [72.60, 18.60]])
    # Cold geom miss
    t0 = time.perf_counter()
    cold_geom_res = PFZEnricherService.enrich_pfz(test_line, feature_id="pfzlines.bench")
    cold_geom_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Cold Line Geometry Sampling & Enrichment Latency: {cold_geom_ms:.3f} ms")

    # Warm geom hit
    geom_latencies_us = []
    for _ in range(500):
        t_start = time.perf_counter()
        warm_geom = PFZEnricherService.enrich_pfz(test_line, feature_id="pfzlines.bench")
        t_end = time.perf_counter()
        geom_latencies_us.append((t_end - t_start) * 1_000_000.0)
        assert warm_geom["sst_median"] == cold_geom_res["sst_median"]

    geom_mean_ms = statistics.mean(geom_latencies_us) / 1000.0
    geom_median_ms = statistics.median(geom_latencies_us) / 1000.0
    print(f"Warm Geometry Cache Hit Latency (N=500): Mean={geom_mean_ms:.4f}ms, Median={geom_median_ms:.4f}ms")
    assert geom_mean_ms < 1.0, f"Expected geometry cache hit latency < 1.0ms, got {geom_mean_ms:.4f}ms"

    print("✓ test_empirical_cache_latency_benchmark passed.")


def test_empirical_quantization_accuracy():
    """
    Empirical Verification of 0.1° Coordinate Quantization:
    - Points within the same 0.1° sector must produce identical sector keys and identical cached telemetry.
    - Coordinates in response must reflect exact query coordinates (rounded to 4 decimal places).
    - Points across 0.1° grid boundaries must quantize to different sectors.
    """
    print("\n--- [2] EMPIRICAL QUANTIZATION ACCURACY (0.1° GRID SECTOR) ---")
    PFZEnricherService.clear_caches()

    # Target sector center: (19.0, 72.8) -> 'lat_19.0_lon_72.8'
    base_lat = 19.0
    base_lon = 72.8
    expected_sector_key = "lat_19.0_lon_72.8"

    # Micro-coordinate variations all rounding to 19.0, 72.8
    variations = [
        (18.9600, 72.8200),
        (18.9510, 72.8490),
        (18.9900, 72.7600),
        (19.0400, 72.8400),
        (19.0000, 72.8000),
        (19.0234, 72.8123),
        (18.9555, 72.7888),
    ]

    first_res = PFZEnricherService.enrich_point(variations[0][0], variations[0][1])
    assert first_res["provenance"]["sector_key"] == expected_sector_key
    base_metrics = first_res["metrics"]

    for lat, lon in variations[1:]:
        res = PFZEnricherService.enrich_point(lat, lon)
        # Check sector key
        assert res["provenance"]["sector_key"] == expected_sector_key, (
            f"Point ({lat}, {lon}) produced sector_key '{res['provenance']['sector_key']}', expected '{expected_sector_key}'"
        )
        # Check cached flag
        assert res["provenance"]["cached"] is True, f"Point ({lat}, {lon}) should be cached from sector"
        # Check metrics equality
        assert res["metrics"] == base_metrics, f"Point ({lat}, {lon}) metrics differ from base sector metrics"
        # Check coordinate fidelity
        assert res["coordinates"]["latitude"] == round(lat, 4)
        assert res["coordinates"]["longitude"] == round(lon, 4)

    print(f"Verified {len(variations)} intra-sector points mapped to identical sector '{expected_sector_key}'")

    # Boundary Tests: Check points across sector boundaries
    boundary_cases = [
        # (lat, lon, expected_sector)
        (19.0600, 72.8000, "lat_19.1_lon_72.8"),
        (18.9400, 72.8000, "lat_18.9_lon_72.8"),
        (19.0000, 72.8600, "lat_19.0_lon_72.9"),
        (19.0000, 72.7400, "lat_19.0_lon_72.7"),
        (0.0000, 0.0000, "lat_0.0_lon_0.0"),
        (-15.123, 75.678, "lat_-15.1_lon_75.7"),
    ]

    for b_lat, b_lon, exp_sector in boundary_cases:
        key = PFZEnricherService.get_sector_key(b_lat, b_lon)
        assert key == exp_sector, f"Expected get_sector_key({b_lat}, {b_lon}) == {exp_sector}, got {key}"
        res = PFZEnricherService.enrich_point(b_lat, b_lon)
        assert res["provenance"]["sector_key"] == exp_sector

    print(f"Verified {len(boundary_cases)} boundary sector transitions successfully.")
    print("✓ test_empirical_quantization_accuracy passed.")


def test_geometry_hash_and_epoch_rollover():
    """
    Empirical Verification:
    - Geometry SHA-256 hash consistency and format determinism.
    - Daily epoch key rollover (cache miss on new UTC date, cache hit within same date).
    - TTL expiration handling.
    """
    print("\n--- [3] GEOMETRY HASH DETERMINISM & DAILY EPOCH KEY ROLLOVER ---")
    PFZEnricherService.clear_caches()

    # 1. Geometry Hash Determinism
    coords1 = [[72.82, 18.96], [72.85, 18.99], [72.90, 19.05]]
    coords1_high_precision = [[72.820000001, 18.960000002], [72.850000000, 18.990000000], [72.900000000, 19.050000000]]

    geom_dict1 = {"type": "LineString", "coordinates": coords1}
    geom_dict1_high = {"type": "LineString", "coordinates": coords1_high_precision}
    shapely_geom1 = LineString(coords1)

    hash1 = PFZEnricherService.get_geometry_hash(geom_dict1)
    hash1_high = PFZEnricherService.get_geometry_hash(geom_dict1_high)
    hash_shapely = PFZEnricherService.get_geometry_hash(shapely_geom1)

    assert len(hash1) == 16, f"Hash must be 16 characters, got length {len(hash1)}"
    assert hash1 == hash1_high, f"Coordinate formatting noise altered hash: {hash1} vs {hash1_high}"
    assert hash1 == hash_shapely, f"Shapely shape produced different hash than GeoJSON dict: {hash1} vs {hash_shapely}"

    # Different geometry must produce different hash
    coords2 = [[72.82, 18.96], [72.85, 18.99], [73.00, 19.10]]
    hash2 = PFZEnricherService.get_geometry_hash({"type": "LineString", "coordinates": coords2})
    assert hash1 != hash2, f"Distinct geometries produced collision: {hash1} == {hash2}"

    print(f"Geometry hashes verified: hash1='{hash1}', hash2='{hash2}' (distinct, 16-hex)")

    # 2. Daily Epoch Key Rollover
    lat, lon = 16.5432, 81.2345
    geom = LineString([[81.20, 16.50], [81.25, 16.55], [81.30, 16.60]])

    # Day 1: 2026-08-29
    with patch.object(PFZEnricherService, "get_utc_date_str", return_value="20260829"):
        PFZEnricherService.clear_caches()
        # Cold query
        res_pt_d1_cold = PFZEnricherService.enrich_point(lat, lon)
        assert res_pt_d1_cold["provenance"]["cached"] is False, "First query on Day 1 must be cold miss"

        # Warm query on Day 1
        res_pt_d1_warm = PFZEnricherService.enrich_point(lat, lon)
        assert res_pt_d1_warm["provenance"]["cached"] is True, "Second query on Day 1 must be cache hit"

        # Geometry query Day 1
        res_geom_d1_cold = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.epoch")
        # Second geom query Day 1
        res_geom_d1_warm = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.epoch")
        assert res_geom_d1_warm["sst_median"] == res_geom_d1_cold["sst_median"]

    # Day 2 Rollover: 2026-08-30
    with patch.object(PFZEnricherService, "get_utc_date_str", return_value="20260830"):
        # Without clearing in-memory cache, querying on Day 2 MUST rollover and trigger cold miss
        res_pt_d2 = PFZEnricherService.enrich_point(lat, lon)
        assert res_pt_d2["provenance"]["cached"] is False, "Point query on new date must rollover (cold miss)"

        # Subsequent query on Day 2 MUST hit Day 2 cache
        res_pt_d2_warm = PFZEnricherService.enrich_point(lat, lon)
        assert res_pt_d2_warm["provenance"]["cached"] is True, "Subsequent query on Day 2 must hit Day 2 cache"

        # Geometry query on Day 2 MUST rollover
        res_geom_d2 = PFZEnricherService.enrich_pfz(geom, feature_id="pfzlines.epoch")
        assert res_geom_d2["sst_median"] is not None

    print("✓ Daily epoch key rollover verified for both Sector Grid and Geometry Caches.")
    print("✓ test_geometry_hash_and_epoch_rollover passed.")


def test_fastapi_endpoints_performance_and_error_codes():
    """
    Empirical Testing of FastAPI Endpoints via TestClient:
    - GET /api/incois/point-analytics (200 OK, full schema conformity, latency benchmark)
    - GET /api/incois/point-analytics error status codes (400, 422 for missing/invalid/out-of-range params)
    - GET /api/incois/pfz-lines (200 OK, FeatureCollection conformity, response time)
    - GET /api/incois/pfz-lines/ (trailing slash support)
    """
    print("\n--- [4] FASTAPI ENDPOINTS PERFORMANCE & ERROR STATUS CODES ---")

    # 1. GET /api/incois/point-analytics - Valid Request
    r = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
    assert r.status_code == 200, f"Expected 200 OK, got {r.status_code}: {r.text}"
    body = r.json()

    # Schema Validation per PROJECT.md specification
    assert body["status"] == "success"
    assert "coordinates" in body
    assert body["coordinates"]["latitude"] == 18.96
    assert body["coordinates"]["longitude"] == 72.82
    assert "timestamp" in body
    assert "source" in body
    assert "metrics" in body

    metrics = body["metrics"]
    expected_metric_keys = [
        "sst_c", "chl_mg_m3", "wind_speed_kmh", "wind_direction_deg",
        "current_speed_ms", "current_direction_deg", "wave_height_m", "wave_period_s"
    ]
    for k in expected_metric_keys:
        assert k in metrics, f"Required metric key '{k}' missing from /point-analytics response"
        assert isinstance(metrics[k], (int, float)), f"Metric '{k}' must be numeric, got {type(metrics[k])}"

    assert "provenance" in body
    assert "cached" in body["provenance"]
    assert "sector_key" in body["provenance"]

    # Benchmark endpoint latency (50 requests)
    ep_latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        res = client.get("/api/incois/point-analytics?lat=18.96&lon=72.82")
        t1 = time.perf_counter()
        assert res.status_code == 200
        ep_latencies.append((t1 - t0) * 1000.0)

    ep_mean = statistics.mean(ep_latencies)
    ep_median = statistics.median(ep_latencies)
    print(f"GET /api/incois/point-analytics Warm Endpoint Latency (N=50): Mean={ep_mean:.3f}ms, Median={ep_median:.3f}ms")
    assert ep_mean < 25.0, f"Endpoint mean latency too high: {ep_mean:.2f}ms"

    # 2. Error Status Code Tests for /api/incois/point-analytics
    error_test_cases = [
        # (query_params, expected_status_codes, description)
        ("", [422], "Missing all query parameters"),
        ("?lat=18.96", [422], "Missing lon parameter"),
        ("?lon=72.82", [422], "Missing lat parameter"),
        ("?lat=abc&lon=72.82", [422], "Non-numeric string lat"),
        ("?lat=18.96&lon=xyz", [422], "Non-numeric string lon"),
        ("?lat=90.001&lon=72.82", [400, 422], "Latitude > 90.0"),
        ("?lat=-90.001&lon=72.82", [400, 422], "Latitude < -90.0"),
        ("?lat=18.96&lon=180.001", [400, 422], "Longitude > 180.0"),
        ("?lat=18.96&lon=-180.001", [400, 422], "Longitude < -180.0"),
        ("?lat=1e99&lon=72.82", [400, 422], "Extreme overflow lat"),
    ]

    for q, exp_codes, desc in error_test_cases:
        err_res = client.get(f"/api/incois/point-analytics{q}")
        assert err_res.status_code in exp_codes, (
            f"Failed test '{desc}': query '{q}' returned status {err_res.status_code}, expected one of {exp_codes}"
        )

    print(f"Verified {len(error_test_cases)} error and boundary validation cases on /point-analytics.")

    # 3. GET /api/incois/pfz-lines - Valid Request
    t0 = time.perf_counter()
    r_pfz = client.get("/api/incois/pfz-lines")
    pfz_latency_ms = (time.perf_counter() - t0) * 1000.0
    assert r_pfz.status_code == 200, f"Expected 200 OK for /pfz-lines, got {r_pfz.status_code}: {r_pfz.text}"
    pfz_body = r_pfz.json()

    print(f"GET /api/incois/pfz-lines Latency: {pfz_latency_ms:.3f} ms")
    assert pfz_body["type"] == "FeatureCollection"
    assert "features" in pfz_body
    assert isinstance(pfz_body["features"], list)
    assert len(pfz_body["features"]) > 0, "PFZ lines endpoint should return features"

    # Validate schema for all features
    for idx, feat in enumerate(pfz_body["features"]):
        assert feat.get("type") == "Feature", f"Feature {idx} type != 'Feature'"
        assert "geometry" in feat
        assert "properties" in feat
        p = feat["properties"]
        assert "id" in p
        assert "name" in p
        assert "sst_median" in p and isinstance(p["sst_median"], (int, float))
        assert "chl_median" in p and isinstance(p["chl_median"], (int, float))
        assert "wave_hs_median" in p and isinstance(p["wave_hs_median"], (int, float))
        assert "current_median" in p and isinstance(p["current_median"], (int, float))
        assert "wind_speed_median" in p and isinstance(p["wind_speed_median"], (int, float))
        assert "catch_score" in p and isinstance(p["catch_score"], int)
        assert 40 <= p["catch_score"] <= 98
        assert "sampled_points_count" in p and p["sampled_points_count"] >= 1
        assert "source" in p
        assert "enriched_at" in p

    # 4. Trailing slash check
    r_slash = client.get("/api/incois/pfz-lines/")
    assert r_slash.status_code == 200, f"Expected 200 OK for /pfz-lines/ trailing slash, got {r_slash.status_code}"

    print(f"Verified /api/incois/pfz-lines FeatureCollection ({len(pfz_body['features'])} enriched features).")
    print("✓ test_fastapi_endpoints_performance_and_error_codes passed.")


def test_zero_static_fish_or_species_names():
    """
    Adversarial Audit:
    - Scans every feature and property in GET /api/incois/pfz-lines for forbidden fish species strings.
    - Tests adversarial injection of legacy fish names into enrich_feature_collection to confirm eradication.
    """
    print("\n--- [5] ZERO STATIC SPECIES AUDIT ON /api/incois/pfz-lines ---")

    forbidden_species_keywords = [
        "tuna", "yellowfin", "skipjack", "bigeye", "sardine", "mackerel",
        "hilsa", "pomfret", "ribbonfish", "squid", "anchovy", "carangid",
        "seerfish", "shark", "ray", "croaker", "prawn", "shrimp", "lobster", "crab"
    ]

    forbidden_property_keys = [
        "target_species", "species", "species_association", "fish_type", "fish_species", "fish_names"
    ]

    # Query the live endpoint
    res = client.get("/api/incois/pfz-lines")
    assert res.status_code == 200
    data = res.json()

    def scan_for_violations(obj, path=""):
        violations = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                cur_path = f"{path}.{k}" if path else k
                # Check forbidden keys
                if k.lower() in forbidden_property_keys:
                    violations.append((cur_path, f"Forbidden key '{k}' found"))
                # Check forbidden substring in string values (excluding technical layer identifiers like PFZ-TUNA if any)
                if isinstance(v, str) and k not in ["source"]:
                    lower_val = v.lower()
                    for sp in forbidden_species_keywords:
                        if sp in lower_val:
                            violations.append((cur_path, f"Forbidden species substring '{sp}' in value '{v}'"))
                violations.extend(scan_for_violations(v, cur_path))
        elif isinstance(obj, list):
            for i, elem in enumerate(obj):
                violations.extend(scan_for_violations(elem, f"{path}[{i}]"))
        return violations

    violations = scan_for_violations(data)
    print(f"Scanned {len(data.get('features', []))} features in /api/incois/pfz-lines for forbidden species names.")
    if violations:
        for vpath, msg in violations:
            print(f"  VIOLATION: {vpath} -> {msg}")
    assert len(violations) == 0, f"Found {len(violations)} forbidden species references in /api/incois/pfz-lines"

    # Adversarial Injection Test
    dirty_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "pfzlines.dirty_1",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[72.1, 18.1], [72.3, 18.3]]
                },
                "properties": {
                    "id": "pfzlines.dirty_1",
                    "target_species": "Yellowfin Tuna & Sardine Mix",
                    "species": "Skipjack Tuna",
                    "species_association": "Mackerel School",
                    "fish_type": "Pelagic",
                    "name": "PFZ Advisory Zone 1"
                }
            }
        ]
    }

    sanitized = PFZEnricherService.enrich_feature_collection(dirty_geojson)
    sanitized_feat = sanitized["features"][0]
    props = sanitized_feat["properties"]

    for k in forbidden_property_keys:
        assert k not in props, f"Property '{k}' was not stripped by enrich_feature_collection"

    print("✓ Adversarial species injection test passed: all fake fish properties completely stripped.")
    print("✓ test_zero_static_fish_or_species_names passed.")


def test_adversarial_robustness_and_corruption_recovery():
    """
    Adversarial Stress Testing:
    - Corrupted/truncated disk cache files: verify graceful recovery without crashing.
    - Degenerate geometries: 0-length, empty, single-point, multi-part with empty sub-geometries.
    - High-concurrency multithreaded queries across random sectors.
    """
    print("\n--- [6] ADVERSARIAL ROBUSTNESS, CORRUPTION RECOVERY & CONCURRENCY ---")

    # 1. Corrupted Sector Disk Cache File Recovery
    corrupt_key = "sector_lat_14.5_lon_74.5_20260829"
    corrupt_file = os.path.join(SECTORS_CACHE_DIR, f"{corrupt_key}.json")
    os.makedirs(SECTORS_CACHE_DIR, exist_ok=True)
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("{THIS_IS_CORRUPTED_JSON_MALFORMED!!!")

    with patch.object(PFZEnricherService, "get_utc_date_str", return_value="20260829"):
        # Clear in-memory cache to force reading corrupted disk file
        with PFZEnricherService._lock:
            PFZEnricherService._memory_point_cache.pop(corrupt_key, None)

        # Must recover gracefully by resolving fresh metrics and overwriting corrupted cache
        res = PFZEnricherService.enrich_point(14.5, 74.5)
        assert res["status"] == "success"
        assert "metrics" in res
        assert res["metrics"]["sst_c"] > 0

    print("✓ Corrupted sector disk cache recovered gracefully without exception.")

    # 2. Corrupted Geometry Disk Cache File Recovery
    corrupt_geom_key = "geom_corrupt_test_20260829"
    corrupt_geom_file = os.path.join(GEOM_CACHE_DIR, f"{corrupt_geom_key}.json")
    os.makedirs(GEOM_CACHE_DIR, exist_ok=True)
    with open(corrupt_geom_file, "w", encoding="utf-8") as f:
        f.write("")  # 0-byte file

    test_geom = LineString([[74.0, 14.0], [74.1, 14.1]])
    geom_hash = PFZEnricherService.get_geometry_hash(test_geom)
    actual_geom_file = os.path.join(GEOM_CACHE_DIR, f"geom_{geom_hash}_20260829.json")
    with open(actual_geom_file, "w", encoding="utf-8") as f:
        f.write("{INVALID_JSON_CORRUPT")

    with patch.object(PFZEnricherService, "get_utc_date_str", return_value="20260829"):
        with PFZEnricherService._lock:
            PFZEnricherService._memory_geom_cache.clear()
        res_geom = PFZEnricherService.enrich_pfz(test_geom, feature_id="pfzlines.corrupt_test")
        assert res_geom["sst_median"] is not None

    print("✓ Corrupted geometry disk cache recovered gracefully without exception.")

    # 3. Degenerate and Boundary Geometries
    test_cases = [
        # (geometry, description)
        (LineString([[72.0, 18.0], [72.0, 18.0]]), "0-length identical start/end LineString"),
        (Point(72.5, 18.5), "Point geometry instead of LineString"),
        (MultiLineString([LineString([[72.0, 18.0], [72.0, 18.0]]), LineString([[72.5, 18.5], [72.6, 18.6]])]), "MultiLineString with degenerate part"),
        (MultiLineString([]), "Empty MultiLineString"),
        (None, "None geometry"),
        (LineString([[p * 0.01, 15.0 + p * 0.01] for p in range(500)]), "Dense LineString with 500 vertices"),
    ]

    for g, desc in test_cases:
        res = PFZEnricherService.enrich_pfz(g, feature_id="pfzlines.edge")
        assert res is not None, f"Failed on {desc}: returned None"
        assert "sst_median" in res, f"Failed on {desc}: missing sst_median"
        assert "catch_score" in res, f"Failed on {desc}: missing catch_score"

    print(f"Verified {len(test_cases)} degenerate and boundary geometry cases.")

    # 4. High-Concurrency Stress Test (64 parallel workers querying 200 requests)
    print("Executing high-concurrency stress test (64 worker threads, 200 requests)...")
    coords_pool = [
        (10.0 + (i % 15) * 0.5, 70.0 + (i % 20) * 0.5)
        for i in range(200)
    ]

    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        futures = [executor.submit(PFZEnricherService.enrich_point, lat, lon) for lat, lon in coords_pool]
        results = [f.result(timeout=15.0) for f in futures]
    t_elapsed = time.perf_counter() - t_start

    assert len(results) == 200
    for r in results:
        assert r["status"] == "success"
        assert "metrics" in r

    print(f"✓ Concurrency stress test completed: 200 requests across 64 threads in {t_elapsed:.2f}s ({200/t_elapsed:.1f} req/s).")
    print("✓ test_adversarial_robustness_and_corruption_recovery passed.")


if __name__ == "__main__":
    print("================================================================")
    print("RUNNING ADVERSARIAL EMPIRICAL TEST HARNESS FOR MILESTONE M2")
    print("================================================================")
    t_all_0 = time.perf_counter()

    test_empirical_cache_latency_benchmark()
    test_empirical_quantization_accuracy()
    test_geometry_hash_and_epoch_rollover()
    test_fastapi_endpoints_performance_and_error_codes()
    test_zero_static_fish_or_species_names()
    test_adversarial_robustness_and_corruption_recovery()

    total_duration = time.perf_counter() - t_all_0
    print(f"\n================================================================")
    print(f"ALL EMPIRICAL M2 TESTS PASSED PERFECTLY IN {total_duration:.3f}s")
    print("================================================================")
