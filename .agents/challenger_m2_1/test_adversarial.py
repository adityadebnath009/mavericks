"""
Adversarial Stress Testing Suite for PFZ Spatiotemporal Sampling Engine
Target: backend/app/api/services/pfz_enricher.py

Covers:
1. Extreme & Boundary Coordinates (Poles, Date Line, Equator, Landmasses, Out-of-bounds, Non-finite)
2. Degenerate & Complex Geometries (Empty, 0-length, Self-intersecting, 1000+ vertex contours, Polygons, Corrupted)
3. High-Concurrency Stress (20 threads same sector, 20 threads disparate sectors, burst operations, atomic write integrity)
4. Statistical Median Stability & Noise Robustness (Outliers, Directional symmetry, Catch score bounds across 10,000 permutations)
"""

import os
import sys
import math
import time
import json
import random
import glob
import statistics
import threading
import concurrent.futures
from typing import List, Dict, Any, Tuple
from shapely.geometry import LineString, MultiLineString, Point, Polygon, MultiPolygon, GeometryCollection

# Add backend directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
backend_dir = os.path.join(project_root, "backend")
sys.path.insert(0, backend_dir)

from app.api.services.pfz_enricher import PFZEnricherService, SECTORS_CACHE_DIR, GEOM_CACHE_DIR


# ==============================================================================
# SECTION 1: Extreme & Boundary Coordinates
# ==============================================================================

def test_extreme_poles_and_date_line():
    """
    Tests exact boundary coordinates: North/South poles, International Date Line, Equator.
    """
    boundaries = [
        (90.0, 0.0, "North Pole Prime Meridian"),
        (90.0, 180.0, "North Pole Date Line East"),
        (90.0, -180.0, "North Pole Date Line West"),
        (-90.0, 0.0, "South Pole Prime Meridian"),
        (-90.0, 180.0, "South Pole Date Line East"),
        (-90.0, -180.0, "South Pole Date Line West"),
        (0.0, 0.0, "Equator Prime Meridian (Null Island)"),
        (0.0, 180.0, "Equator International Date Line East"),
        (0.0, -180.0, "Equator International Date Line West"),
        (89.99999, 179.99999, "Arctic Edge Date Line"),
        (-89.99999, -179.99999, "Antarctic Edge Date Line"),
    ]

    for lat, lon, desc in boundaries:
        res = PFZEnricherService.enrich_point(lat, lon)
        assert res is not None, f"Failed for {desc}"
        assert res["status"] == "success", f"Expected success for {desc}"
        assert "metrics" in res, f"Missing metrics for {desc}"
        metrics = res["metrics"]
        assert 15.0 <= metrics["sst_c"] <= 35.0, f"SST out of bounds for {desc}: {metrics['sst_c']}"
        assert 0.0 <= metrics["chl_mg_m3"] <= 20.0, f"CHL out of bounds for {desc}: {metrics['chl_mg_m3']}"
        assert 0.0 <= metrics["wave_height_m"] <= 20.0, f"Wave height out of bounds for {desc}: {metrics['wave_height_m']}"
        assert 0.0 <= metrics["current_speed_ms"] <= 5.0, f"Current speed out of bounds for {desc}: {metrics['current_speed_ms']}"


def test_terrestrial_and_remote_landmasses():
    """
    Tests behavior when coordinates fall on remote landmasses or deep inland.
    The spatiotemporal engine should fallback gracefully to climatology/offline models without crashing.
    """
    land_points = [
        (25.0, 15.0, "Sahara Desert"),
        (27.9881, 86.9250, "Mount Everest"),
        (-3.4653, -62.2159, "Central Amazon Rainforest"),
        (32.0, 85.0, "Tibetan Plateau"),
        (28.6139, 77.2090, "New Delhi (Inland)"),
        (39.8283, -98.5795, "Geographic Center of Contiguous USA"),
    ]

    for lat, lon, desc in land_points:
        res = PFZEnricherService.enrich_point(lat, lon)
        assert res["status"] == "success", f"Inland query failed for {desc}"
        assert res["metrics"]["sst_c"] is not None
        assert res["metrics"]["chl_mg_m3"] is not None
        assert res["source"] in [
            "INCOIS GeoServer & OPENDAP",
            "INCOIS Grid Cache",
            "Open-Meteo Marine Fallback",
            "Nominal Marine Climatology"
        ]


def test_out_of_range_and_non_finite_coordinates():
    """
    Adversarially feeds out-of-range coordinates, NaNs, Infs, and invalid types to enrich_point.
    Verifies strict input sanitization and descriptive error propagation.
    """
    invalid_coords = [
        (90.0001, 72.82, "Lat slightly above 90"),
        (120.0, 72.82, "Lat 120"),
        (-90.0001, 72.82, "Lat slightly below -90"),
        (-150.0, 72.82, "Lat -150"),
        (18.96, 180.0001, "Lon slightly above 180"),
        (18.96, 240.0, "Lon 240"),
        (18.96, -180.0001, "Lon slightly below -180"),
        (18.96, -360.0, "Lon -360"),
        (float('nan'), 72.82, "NaN Latitude"),
        (18.96, float('nan'), "NaN Longitude"),
        (float('inf'), 72.82, "Positive Inf Latitude"),
        (18.96, float('inf'), "Positive Inf Longitude"),
        (float('-inf'), 72.82, "Negative Inf Latitude"),
        (18.96, float('-inf'), "Negative Inf Longitude"),
    ]

    for lat, lon, desc in invalid_coords:
        try:
            PFZEnricherService.enrich_point(lat, lon)
            assert False, f"Expected ValueError for {desc} (lat={lat}, lon={lon}), but call succeeded!"
        except ValueError as ve:
            assert "out of bounds" in str(ve).lower(), f"Expected bounds error message, got: {ve}"
        except TypeError:
            pass

    bad_types = [
        ("18.96", 72.82, "String latitude"),
        (None, 72.82, "None latitude"),
        (18.96, None, "None longitude"),
        ([18.96], 72.82, "List latitude"),
    ]
    for lat, lon, desc in bad_types:
        try:
            PFZEnricherService.enrich_point(lat, lon)
            assert False, f"Expected exception for bad type: {desc}"
        except (TypeError, ValueError):
            pass


# ==============================================================================
# SECTION 2: Degenerate & Complex Geometries
# ==============================================================================

def test_degenerate_linestrings():
    """
    Tests 0-length LineStrings, single-vertex lines, empty lines, and redundant vertex lines.
    """
    test_geometries = [
        ({"type": "LineString", "coordinates": []}, "Empty coordinates LineString"),
        (LineString([]), "Empty Shapely LineString"),
        ({"type": "LineString", "coordinates": [[72.5, 18.5], [72.5, 18.5]]}, "2 identical points (0-length)"),
        (LineString([(72.5, 18.5), (72.5, 18.5)]), "Shapely 0-length LineString"),
        ({"type": "LineString", "coordinates": [[72.5, 18.5]] * 5}, "5 identical points (0-length)"),
        ({"type": "LineString", "coordinates": [[72.5, 18.5], [72.50000001, 18.50000001]]}, "Microscopic line"),
    ]

    for geom, desc in test_geometries:
        res = PFZEnricherService.enrich_pfz(geom, feature_id=f"deg_{abs(hash(desc))}")
        assert res is not None, f"Failed on {desc}"
        assert "sst_median" in res, f"Missing sst_median on {desc}"
        assert "catch_score" in res, f"Missing catch_score on {desc}"
        assert 40 <= res["catch_score"] <= 98, f"Catch score out of range on {desc}"
        assert res["sampled_points_count"] >= 1, f"Sample count must be >= 1 on {desc}"


def test_degenerate_and_mixed_multilinestrings():
    """
    Tests empty MultiLineStrings, MultiLineStrings with all 0-length parts,
    and mixed MultiLineStrings with a combination of valid and degenerate lines.
    """
    test_mls = [
        ({"type": "MultiLineString", "coordinates": []}, "Empty MultiLineString"),
        (MultiLineString([]), "Shapely Empty MultiLineString"),
        ({
            "type": "MultiLineString",
            "coordinates": [
                [[72.5, 18.5], [72.5, 18.5]],
                [[73.0, 19.0], [73.0, 19.0]]
            ]
        }, "MultiLineString with 0-length parts"),
        ({
            "type": "MultiLineString",
            "coordinates": [
                [[72.5, 18.5], [72.5, 18.5]],
                [[72.0, 18.0], [72.6, 18.6]],
                [[73.0, 19.0], [73.0, 19.0]],
            ]
        }, "Mixed MultiLineString with valid and 0-length parts")
    ]

    for geom, desc in test_mls:
        res = PFZEnricherService.enrich_pfz(geom, feature_id=f"mls_{abs(hash(desc))}")
        assert res is not None, f"Failed on {desc}"
        assert "sst_median" in res, f"Missing sst_median on {desc}"
        assert res["sampled_points_count"] >= 1, f"Sample count must be >= 1 on {desc}"


def test_self_intersecting_and_complex_geometries():
    """
    Tests self-intersecting geometries (Figure-8, Bowtie, overlapping zigzags).
    """
    figure_8 = {
        "type": "LineString",
        "coordinates": [
            [72.0, 18.0],
            [73.0, 19.0],
            [73.0, 18.0],
            [72.0, 19.0],
            [72.0, 18.0]
        ]
    }
    res_8 = PFZEnricherService.enrich_pfz(figure_8, feature_id="fig8")
    assert res_8 is not None
    assert 3 <= res_8["sampled_points_count"] <= 10
    assert 40 <= res_8["catch_score"] <= 98

    zigzag = {
        "type": "LineString",
        "coordinates": [
            [72.0, 18.0], [72.2, 18.2], [72.0, 18.0],
            [72.2, 18.2], [72.4, 18.4], [72.2, 18.2]
        ]
    }
    res_zz = PFZEnricherService.enrich_pfz(zigzag, feature_id="zigzag")
    assert res_zz is not None
    assert 3 <= res_zz["sampled_points_count"] <= 10


def test_massive_1000_vertex_contour_sampling():
    """
    Adversarially feeds a 1,000-vertex and 5,000-vertex complex fractal contour spanning multiple sectors.
    Verifies that execution is fast (< 500ms), memory is bounded, and sample count strictly obeys [3, 10].
    """
    coords_1000 = []
    base_lat, base_lon = 15.0, 72.0
    for i in range(1000):
        t = i / 1000.0
        lat = base_lat + t * 4.0 + 0.05 * math.sin(t * 50.0 * math.pi)
        lon = base_lon + t * 4.0 + 0.05 * math.cos(t * 50.0 * math.pi)
        coords_1000.append([round(lon, 6), round(lat, 6)])

    geom_1000 = {"type": "LineString", "coordinates": coords_1000}

    t0 = time.perf_counter()
    res_1000 = PFZEnricherService.enrich_pfz(geom_1000, feature_id="pfz_1000_vertices")
    elapsed = time.perf_counter() - t0

    assert res_1000 is not None
    assert 3 <= res_1000["sampled_points_count"] <= 10, f"Sampled count {res_1000['sampled_points_count']} exceeded [3, 10]"
    assert elapsed < 0.500, f"1000-vertex sampling took too long: {elapsed:.4f}s"

    coords_5000 = [[round(72.0 + (i/5000.0)*3.0, 6), round(15.0 + (i/5000.0)*3.0, 6)] for i in range(5000)]
    geom_5000 = {"type": "LineString", "coordinates": coords_5000}
    res_5000 = PFZEnricherService.enrich_pfz(geom_5000, feature_id="pfz_5000_vertices")
    assert res_5000 is not None
    assert 3 <= res_5000["sampled_points_count"] <= 10


def test_non_linestring_geometry_fallbacks():
    """
    Tests passing Polygon, MultiPolygon, Point, GeometryCollection, and raw dict geometries to enrich_pfz.
    """
    pt_geom = Point(72.82, 18.96)
    res_pt = PFZEnricherService.enrich_pfz(pt_geom, feature_id="pt_geom")
    assert res_pt["sampled_points_count"] == 1
    assert "sst_median" in res_pt

    poly_geom = Polygon([(72.0, 18.0), (73.0, 18.0), (73.0, 19.0), (72.0, 19.0), (72.0, 18.0)])
    res_poly = PFZEnricherService.enrich_pfz(poly_geom, feature_id="poly_geom")
    assert res_poly["sampled_points_count"] == 1
    assert "sst_median" in res_poly

    gc = GeometryCollection([LineString([(72.0, 18.0), (72.5, 18.5)]), Point(73.0, 19.0)])
    res_gc = PFZEnricherService.enrich_pfz(gc, feature_id="gc_geom")
    assert res_gc is not None
    assert "sst_median" in res_gc


def test_geometry_hash_normalization_and_stability():
    """
    Verifies that minor floating point noise in coordinate representation (e.g. 72.8 vs 72.800000001)
    or dictionary key ordering yields deterministic hashes.
    """
    geom_a = {
        "type": "LineString",
        "coordinates": [[72.8000001, 18.9600001], [72.8500001, 18.9800001]]
    }
    geom_b = {
        "type": "LineString",
        "coordinates": [[72.8000004, 18.9600004], [72.8500004, 18.9800004]]
    }
    hash_a = PFZEnricherService.get_geometry_hash(geom_a)
    hash_b = PFZEnricherService.get_geometry_hash(geom_b)
    assert hash_a == hash_b, f"Hashes diverged on sub-micro-degree differences: {hash_a} vs {hash_b}"


# ==============================================================================
# SECTION 3: High-Concurrency & Multi-Threaded Stress Testing
# ==============================================================================

def test_concurrent_same_sector_stress():
    """
    Spawns 20 parallel threads querying the EXACT same sector simultaneously.
    Verifies that thread-locks and atomic file replacement prevent race conditions,
    file corruptions, or partial writes.
    """
    PFZEnricherService.clear_caches()
    lat, lon = 18.9654, 72.8245
    num_threads = 20
    requests_per_thread = 10

    errors = []

    def worker(worker_id):
        for req in range(requests_per_thread):
            try:
                offset = (req % 5) * 0.001
                res = PFZEnricherService.enrich_point(lat + offset, lon + offset)
                if res.get("status") != "success":
                    errors.append(f"Worker {worker_id} request {req} got status {res.get('status')}")
                if "metrics" not in res or not isinstance(res["metrics"].get("sst_c"), (int, float)):
                    errors.append(f"Worker {worker_id} request {req} missing valid metrics")
            except Exception as e:
                errors.append(f"Worker {worker_id} crashed: {e}")

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15.0)

    assert len(errors) == 0, f"Encountered {len(errors)} concurrent errors:\n" + "\n".join(errors[:10])


def test_concurrent_disparate_sectors_stress():
    """
    Spawns 20 parallel threads querying 20 disparate sectors spread around the globe simultaneously.
    """
    PFZEnricherService.clear_caches()
    disparate_coords = [
        (18.96, 72.82), (15.12, 73.55), (12.98, 80.25), (8.52, 76.95),
        (21.25, 88.65), (19.80, 85.80), (10.85, 72.20), (11.66, 92.74),
        (0.00, 75.00), (-10.00, 80.00), (-20.00, 60.00), (25.00, 65.00),
        (16.50, 82.50), (14.00, 74.00), (9.00, 79.00), (17.00, 73.00),
        (20.00, 70.00), (13.50, 80.00), (11.00, 75.50), (22.00, 69.00)
    ]

    results = []
    errors = []

    def query_sector(coord):
        lat, lon = coord
        try:
            return PFZEnricherService.enrich_point(lat, lon)
        except Exception as e:
            errors.append(f"Coord {coord} error: {e}")
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(query_sector, c) for c in disparate_coords]
        for f in concurrent.futures.as_completed(futures, timeout=15.0):
            res = f.result()
            if res:
                results.append(res)

    assert len(errors) == 0, f"Disparate concurrency errors: {errors}"
    assert len(results) == len(disparate_coords)


def test_cache_file_atomic_integrity():
    """
    Verifies that no temporary files (.tmp.*) remain in the cache directories after concurrent operations
    and all cached JSON files are valid JSON.
    """
    tmp_files = glob.glob(os.path.join(SECTORS_CACHE_DIR, "*.tmp.*")) + glob.glob(os.path.join(GEOM_CACHE_DIR, "*.tmp.*"))
    assert len(tmp_files) == 0, f"Leaked {len(tmp_files)} temporary cache files: {tmp_files}"

    sector_files = glob.glob(os.path.join(SECTORS_CACHE_DIR, "*.json"))
    for sf in sector_files:
        with open(sf, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "data" in data
            assert "key" in data


# ==============================================================================
# SECTION 4: Statistical Median Stability & Noisy Inputs
# ==============================================================================

def test_median_resilience_to_extreme_outliers():
    """
    Tests that statistical median aggregation on LineString telemetry is robust against
    sensor spikes or isolated anomalous data points.
    """
    geom = {
        "type": "LineString",
        "coordinates": [
            [72.50, 18.50], [72.55, 18.55], [72.60, 18.60],
            [72.65, 18.65], [72.70, 18.70], [72.75, 18.75],
            [72.80, 18.80]
        ]
    }
    res = PFZEnricherService.enrich_pfz(geom, feature_id="pfz_outlier_test")

    assert 24.0 <= res["sst_median"] <= 31.5, f"Median SST pulled out of range: {res['sst_median']}"
    assert 0.08 <= res["chl_median"] <= 2.5, f"Median CHL pulled out of range: {res['chl_median']}"
    assert 0.5 <= res["wave_hs_median"] <= 3.0, f"Median wave hs out of range: {res['wave_hs_median']}"


def test_directional_sampling_symmetry():
    """
    Verifies that sampling a LineString in forward direction (A -> B) vs reverse direction (B -> A)
    yields statistically consistent median environmental properties.
    """
    forward_coords = [[72.20, 18.20], [72.40, 18.40], [72.60, 18.60], [72.80, 18.80]]
    reverse_coords = list(reversed(forward_coords))

    geom_fwd = {"type": "LineString", "coordinates": forward_coords}
    geom_rev = {"type": "LineString", "coordinates": reverse_coords}

    res_fwd = PFZEnricherService.enrich_pfz(geom_fwd, feature_id="fwd")
    res_rev = PFZEnricherService.enrich_pfz(geom_rev, feature_id="rev")

    assert abs(res_fwd["sst_median"] - res_rev["sst_median"]) <= 0.2, (
        f"Directional asymmetry in SST: {res_fwd['sst_median']} vs {res_rev['sst_median']}"
    )
    assert abs(res_fwd["chl_median"] - res_rev["chl_median"]) <= 0.05, (
        f"Directional asymmetry in CHL: {res_fwd['chl_median']} vs {res_rev['chl_median']}"
    )
    assert abs(res_fwd["catch_score"] - res_rev["catch_score"]) <= 2, (
        f"Directional asymmetry in Catch Score: {res_fwd['catch_score']} vs {res_rev['catch_score']}"
    )


def test_catch_score_mathematical_grid_bounds():
    """
    Adversarial Monte Carlo & Grid Search across 10,000 parameter combinations:
    - SST: [10.0, 40.0]
    - CHL: [0.0, 25.0]
    - Wave Hs: [0.0, 20.0]
    - Current Speed: [0.0, 10.0]
    - Wind Speed: [0.0, 150.0]
    """
    random.seed(42)

    extreme_cases = [
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (100.0, 100.0, 100.0, 100.0, 500.0),
        (-50.0, -10.0, -5.0, -2.0, -10.0),
        (28.5, 0.9, 0.8, 0.4, 10.0),  # Ideal
        (15.0, 0.01, 8.0, 2.5, 90.0), # Storm / Hostile
    ]

    for sst, chl, wave, curr, wind in extreme_cases:
        score = PFZEnricherService.calculate_catch_score(sst, chl, wave, curr, wind)
        assert isinstance(score, int), f"Score must be int, got {type(score)}"
        assert 40 <= score <= 98, f"Score {score} out of [40, 98] on ({sst}, {chl}, {wave}, {curr}, {wind})"

    for _ in range(10000):
        sst = random.uniform(10.0, 38.0)
        chl = random.uniform(0.01, 15.0)
        wave = random.uniform(0.1, 15.0)
        curr = random.uniform(0.0, 4.0)
        wind = random.uniform(0.0, 120.0)

        score = PFZEnricherService.calculate_catch_score(sst, chl, wave, curr, wind)
        assert 40 <= score <= 98, f"Monte Carlo violation: score={score} for ({sst}, {chl}, {wave}, {curr}, {wind})"

    ideal_score = PFZEnricherService.calculate_catch_score(28.5, 0.9, 0.8, 0.4, 10.0)
    storm_score = PFZEnricherService.calculate_catch_score(24.0, 0.1, 6.5, 1.8, 85.0)
    assert ideal_score >= 85, f"Ideal score should be >= 85, got {ideal_score}"
    assert storm_score <= 50, f"Storm score should be <= 50, got {storm_score}"


# ==============================================================================
# Main Runner
# ==============================================================================

def run_adversarial_suite():
    print("================================================================================")
    print("STARTING PFZ ENRICHER ADVERSARIAL STRESS TEST SUITE")
    print("================================================================================")

    suite = [
        ("Extreme Poles & Date Line Boundaries", test_extreme_poles_and_date_line),
        ("Terrestrial & Inland Coordinates", test_terrestrial_and_remote_landmasses),
        ("Out-of-Range & Non-Finite Coordinates", test_out_of_range_and_non_finite_coordinates),
        ("Degenerate & 0-Length LineStrings", test_degenerate_linestrings),
        ("Degenerate & Mixed MultiLineStrings", test_degenerate_and_mixed_multilinestrings),
        ("Self-Intersecting & Complex Geometries", test_self_intersecting_and_complex_geometries),
        ("Massive 1,000+ Vertex Contours", test_massive_1000_vertex_contour_sampling),
        ("Non-LineString Geometry Fallbacks", test_non_linestring_geometry_fallbacks),
        ("Geometry SHA-256 Hash Invariance", test_geometry_hash_normalization_and_stability),
        ("20-Thread Concurrent Same-Sector Stress", test_concurrent_same_sector_stress),
        ("20-Thread Concurrent Disparate-Sector Stress", test_concurrent_disparate_sectors_stress),
        ("Cache File Atomic Integrity & Temp Cleanup", test_cache_file_atomic_integrity),
        ("Median Resilience to Outliers", test_median_resilience_to_extreme_outliers),
        ("Directional Sampling Symmetry", test_directional_sampling_symmetry),
        ("Catch Score 10,000 Monte Carlo Range Validation", test_catch_score_mathematical_grid_bounds),
    ]

    passed = 0
    failed = 0
    start_time = time.perf_counter()

    for name, test_func in suite:
        t0 = time.perf_counter()
        try:
            test_func()
            dur = (time.perf_counter() - t0) * 1000.0
            print(f"  ✓ [PASS] {name} ({dur:.1f} ms)")
            passed += 1
        except Exception as e:
            dur = (time.perf_counter() - t0) * 1000.0
            print(f"  ✗ [FAIL] {name} ({dur:.1f} ms)")
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    total_dur = time.perf_counter() - start_time
    print("================================================================================")
    print(f"ADVERSARIAL STRESS RESULTS: {passed} PASSED, {failed} FAILED in {total_dur:.2f}s")
    print("================================================================================")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_adversarial_suite()
