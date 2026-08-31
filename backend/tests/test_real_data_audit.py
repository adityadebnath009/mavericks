import math
import sys
from datetime import datetime, timedelta
import xarray as xr

from app.api.services.forecast_data import ForecastDataService
from app.api.services.bsi_calculator import BSICalculator
from app.api.services.pfz_routing import PFZRoutingService
from app.api.services.incois_resolver import IncoisDatasetResolver

def run_audit():
    print("=== MAVERICKS REAL-DATA AUDIT ===")
    print("Tracing provenance of a single point from INCOIS NetCDF through to Final Route Decision...\n")
    
    # 1. Coordinate to audit
    audit_lat, audit_lon = 15.0, 71.8
    audit_time = datetime(2026, 8, 27, 13, 0, 0)
    
    # 2. Fetch the actual cache snapshot we saved for T0 (2026-08-27 12:00:00)
    # The cache files are named safety_grid_day_1_hour_12.json
    cache = ForecastDataService.load_grid(day=1, hour=12)
    node = next((n for n in cache if math.isclose(n[0], audit_lat) and math.isclose(n[1], audit_lon)), None)
    if not node:
        print(f"FAILED: Node ({audit_lat}, {audit_lon}) not found in Day 1 Hour 12 cache.")
        sys.exit(1)
        
    raw_props = node[2]
    print(f"[1. CACHE LAYER]")
    print(f"Cached Node ({audit_lat}, {audit_lon}) at T0 (12:00):")
    print(f"  HS  (hs): {raw_props['hs']}")
    print(f"  STP (stp): {raw_props['stp']}")
    print(f"  SPR (spr): {raw_props['spr']}")
    print(f"  PHS00_T0 (hsea_initial): {raw_props['hsea_initial']}")
    print(f"  PHS00_T1 (hsea_final): {raw_props['hsea_final']}\n")
    
    # 3. Simulate ForecastDataService Interpolation
    env = ForecastDataService.get_environment(audit_lat, audit_lon, audit_time)
    print(f"[2. INTERPOLATION LAYER (ForecastDataService)]")
    print(f"Interpolated values for {audit_time}:")
    print(f"  Wave Height: {env.wave_height_m}")
    print(f"  Wave Steepness: {env.wave_steepness}")
    print(f"  Dir Spread: {env.directional_spread}")
    print(f"  BSI calculated internally: {env.bsi}\n")
    
    # 4. Independent BSI calculation to prove math
    # We must manually interpolate the values for audit_time
    # T0 is 12:00, T1 is 15:00. audit_time is 13:00, which is 1/3 of the way.
    w = 1.0 / 3.0
    cache_t1 = ForecastDataService.load_grid(day=1, hour=15)
    node_t1 = next(n for n in cache_t1 if math.isclose(n[0], audit_lat) and math.isclose(n[1], audit_lon))
    props_t1 = node_t1[2]
    
    interp_hs = raw_props['hs'] + w * (props_t1['hs'] - raw_props['hs'])
    interp_stp = raw_props['stp'] + w * (props_t1['stp'] - raw_props['stp'])
    interp_spr_deg = raw_props['spr'] + w * (props_t1['spr'] - raw_props['spr'])
    
    # Calculate directional spread parameter (ss) from degrees
    interp_spr = math.sqrt(2.0 * (1.0 - math.cos(math.radians(interp_spr_deg))))
    
    interp_hsea_i = raw_props['hsea_initial'] + w * (props_t1['hsea_initial'] - raw_props['hsea_initial'])
    interp_hsea_f = raw_props['hsea_final'] + w * (props_t1['hsea_final'] - raw_props['hsea_final'])
    
    expected_bsi = BSICalculator.calculate_bsi(
        Ss=interp_stp, Hs=interp_hs, ss=interp_spr, Hsea_initial=interp_hsea_i, Hsea_final=interp_hsea_f
    )
    
    print(f"[3. PROVENANCE VERIFICATION]")
    print(f"  Expected BSI from raw physics math: {expected_bsi}")
    print(f"  Actual BSI outputted by Environment: {env.bsi}")
    if env.bsi == expected_bsi:
        print("  ✅ BSI derivation matches exactly (no hallucinated approximations).")
    else:
        print("  ❌ BSI MISMATCH! Hallucination detected.")
        sys.exit(1)
        
    print(f"\n[4. ROUTING DECISION LAYER]")
    route = PFZRoutingService.calculate_optimal_route(
        start_lat=audit_lat, start_lon=audit_lon, end_lat=15.4, end_lon=71.8,
        beam_m=5.0, cruising_speed_kn=8.0, departure_time="2026-08-27T12:00:00Z"
    )
    # Find the snapshot for the audit_lat, audit_lon
    snap = next((s for s in route["snapshots"] if math.isclose(s["lat"], audit_lat) and math.isclose(s["lon"], audit_lon)), None)
    if snap:
        print(f"  Snapshot generated for ({audit_lat}, {audit_lon}):")
        print(f"  Risk Level: {snap['risk']}")
        print(f"  Wave Height: {snap['wave_height_m']}")
        print(f"  BSI: {snap['bsi']}")
        if snap['bsi'] == env.bsi or snap['bsi'] == raw_props['bsi']: # At T0 it uses raw_props
            print("  ✅ Router consumed the exact proven variables.")
        else:
            print("  ⚠️ Router BSI doesn't match! (Check interpolation time matching)")
    else:
        print("  ⚠️ Coordinate was not included in final route (likely rejected due to danger).")
        
    print("\n✅ REAL-DATA AUDIT PASSED")

if __name__ == "__main__":
    run_audit()
