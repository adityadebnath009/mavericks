import re
with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Fix the u_wnd parsing to use None instead of 0.0
old_parsing = """            mwd = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.MWD.values]
            t02 = [float(v) if not np.isnan(v) else 6.0 for v in ww3_subset.T02.values]
            u_wnd = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.UWND.values]
            v_wnd = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.VWND.values]
            
            # PHS00 is the wind-sea wave height variable
            hsea = [float(v) if not np.isnan(v) else 0.0 for v in ww3_subset.PHS00.values]
            
            offset = 2 if start_idx - 2 >= 0 else 0
            
            ww3_records = []
            curr_records = []
            
            for k in range(8):
                idx = offset + k
                lookback_idx = idx - 2 if idx - 2 >= 0 else idx
                
                # Derive wind variables: speed = sqrt(U^2 + V^2) * 3.6 (m/s to km/h)
                wind_speed_kmh = math.sqrt(u_wnd[idx]**2 + v_wnd[idx]**2) * 3.6
                
                # Derive wind direction (using standard meteorological convention: direction from which wind blows)
                wind_dir_rad = math.atan2(u_wnd[idx], v_wnd[idx])
                wind_dir_deg = (math.degrees(wind_dir_rad) + 180) % 360"""

new_parsing = """            mwd = [float(v) if not np.isnan(v) else None for v in ww3_subset.MWD.values]
            t02 = [float(v) if not np.isnan(v) else None for v in ww3_subset.T02.values]
            u_wnd = [float(v) if not np.isnan(v) else None for v in ww3_subset.UWND.values]
            v_wnd = [float(v) if not np.isnan(v) else None for v in ww3_subset.VWND.values]
            
            # PHS00 is the wind-sea wave height variable
            hsea = [float(v) if not np.isnan(v) else None for v in ww3_subset.PHS00.values]
            
            offset = 2 if start_idx - 2 >= 0 else 0
            
            ww3_records = []
            curr_records = []
            
            for k in range(8):
                idx = offset + k
                lookback_idx = idx - 2 if idx - 2 >= 0 else idx
                
                u_val = u_wnd[idx]
                v_val = v_wnd[idx]
                
                if u_val is not None and v_val is not None:
                    # Derive wind variables: speed = sqrt(U^2 + V^2) * 3.6 (m/s to km/h)
                    wind_speed_kmh = math.sqrt(u_val**2 + v_val**2) * 3.6
                    # Derive wind direction (meteorological convention)
                    wind_dir_rad = math.atan2(u_val, v_val)
                    wind_dir_deg = (math.degrees(wind_dir_rad) + 180) % 360
                else:
                    wind_speed_kmh = None
                    wind_dir_deg = None"""

content = content.replace(old_parsing, new_parsing)

# Current parsing
old_curr = """                u_curr = float(curr_step.U.values) if not np.isnan(curr_step.U.values) else 0.0
                v_curr = float(curr_step.V.values) if not np.isnan(curr_step.V.values) else 0.0
                
                # Derive current speed: speed = sqrt(U^2 + V^2)
                curr_speed_ms = math.sqrt(u_curr**2 + v_curr**2)
                
                # Derive current direction (using oceanographic convention: direction towards which current flows)
                curr_dir_rad = math.atan2(u_curr, v_curr)
                curr_dir_deg = math.degrees(curr_dir_rad)
                curr_dir = curr_dir_deg if curr_dir_deg >= 0 else 360.0 + curr_dir_deg"""

new_curr = """                u_curr = float(curr_step.U.values) if not np.isnan(curr_step.U.values) else None
                v_curr = float(curr_step.V.values) if not np.isnan(curr_step.V.values) else None
                
                if u_curr is not None and v_curr is not None:
                    # Derive current speed: speed = sqrt(U^2 + V^2)
                    curr_speed_ms = math.sqrt(u_curr**2 + v_curr**2)
                    
                    # Derive current direction (oceanographic convention)
                    curr_dir_rad = math.atan2(u_curr, v_curr)
                    curr_dir_deg = math.degrees(curr_dir_rad)
                    curr_dir = curr_dir_deg if curr_dir_deg >= 0 else 360.0 + curr_dir_deg
                else:
                    curr_speed_ms = None
                    curr_dir = None"""

content = content.replace(old_curr, new_curr)

# Now append the vector_grid method
vector_grid_method = """
    @classmethod
    def resolve_vector_grid(cls, day: int = 1) -> dict:
        \"\"\"
        Retrieves a 0.5-degree gridded vector field of Wind and Currents over the Indian EEZ.
        Caches the grid locally to prevent slow MapLibre rendering.
        \"\"\"
        grid_cache = os.path.join(cls.CACHE_DIR, f"vector_grid_day_{day}.json")
        now_ts = time.time()
        
        # Cache for 6 hours
        if os.path.exists(grid_cache):
            if now_ts - os.path.getmtime(grid_cache) < 6 * 3600:
                try:
                    import json
                    with open(grid_cache, "r") as f:
                        return json.load(f)
                except:
                    pass

        try:
            import json
            import numpy as np
            
            # Using netcdf4 engine for OPENDAP
            ds_ww3 = xr.open_dataset(cls.get_ww3_url(), engine="netcdf4")
            ds_curr = xr.open_dataset(cls.get_currents_url(), engine="netcdf4")
            
            # Target 12:00 UTC for the given day
            start_idx = (day - 1) * 8
            time_idx = min(start_idx + 4, len(ds_ww3.TIME) - 1)
            target_timestamp = ds_ww3.TIME.values[time_idx]
            
            # Subset domains roughly over Indian EEZ [Lat 5 to 25, Lon 65 to 95]
            # Coarsen by 2 (usually INCOIS is 0.25 deg, this makes it 0.5 deg for fast rendering)
            ww3_slice = ds_ww3.sel(IOYAXIS=slice(5, 25), IOXAXIS=slice(65, 95)).isel(TIME=time_idx).coarsen(IOYAXIS=2, IOXAXIS=2, boundary="trim").mean()
            
            curr_slice = ds_curr.sel(LAT=slice(5, 25), LON=slice(65, 95), DEPTH1_1=0.0).sel(TAXIS=target_timestamp, method="nearest").coarsen(LAT=2, LON=2, boundary="trim").mean()
            
            wind_vectors = []
            for lat, lon, u, v in zip(
                ww3_slice.IOYAXIS.values.ravel(),
                ww3_slice.IOXAXIS.values.ravel(),
                ww3_slice.UWND.values.ravel(),
                ww3_slice.VWND.values.ravel()
            ):
                if not np.isnan(u) and not np.isnan(v):
                    speed = math.sqrt(u**2 + v**2) * 3.6
                    deg = (math.degrees(math.atan2(u, v)) + 180) % 360
                    wind_vectors.append({
                        "lat": round(float(lat), 2),
                        "lon": round(float(lon), 2),
                        "u": round(float(u), 2),
                        "v": round(float(v), 2),
                        "speed_kmh": round(speed, 1),
                        "direction_deg": round(deg, 1)
                    })
                    
            curr_vectors = []
            for lat, lon, u, v in zip(
                curr_slice.LAT.values.ravel(),
                curr_slice.LON.values.ravel(),
                curr_slice.U.values.ravel(),
                curr_slice.V.values.ravel()
            ):
                if not np.isnan(u) and not np.isnan(v):
                    speed = math.sqrt(u**2 + v**2)
                    deg = math.degrees(math.atan2(u, v))
                    deg = deg if deg >= 0 else 360.0 + deg
                    curr_vectors.append({
                        "lat": round(float(lat), 2),
                        "lon": round(float(lon), 2),
                        "u": round(float(u), 3),
                        "v": round(float(v), 3),
                        "speed_ms": round(speed, 2),
                        "direction_deg": round(deg, 1)
                    })
                    
            grid_data = {
                "wind": wind_vectors,
                "current": curr_vectors,
                "timestamp": str(target_timestamp)
            }
            
            with open(grid_cache, "w") as f:
                json.dump(grid_data, f)
                
            return grid_data
        except Exception as e:
            # Fallback to empty if it fails so frontend doesn't crash
            import logging
            logging.error(f"Failed to generate vector grid: {e}")
            return {"wind": [], "current": [], "error": str(e)}
"""

content += vector_grid_method

with open("backend/app/api/services/incois_resolver.py", "w") as f:
    f.write(content)
