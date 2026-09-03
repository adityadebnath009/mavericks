import re
with open("backend/app/api/services/incois_resolver.py", "r") as f:
    content = f.read()

# Change resolve_latest_forecast signature
content = content.replace(
    "def resolve_latest_forecast(cls, lat: float, lon: float, day: int) -> Tuple[ForecastResult, ForecastResult]:",
    "def resolve_latest_forecast(cls, lat: float, lon: float, day: int, purpose: str = 'routing') -> Tuple[ForecastResult, ForecastResult]:"
)

# Insert stale cache fallback after remote fetch failure
fetch_block = """            except Exception as e:
                raise RuntimeError(f"INCOIS Remote fetch error: {e}") from e"""

stale_fallback_block = """            except Exception as e:
                if purpose == "visualization":
                    import glob
                    ww3_pattern = os.path.join(cls.CACHE_DIR, "ww3", f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_*.pkl")
                    curr_pattern = os.path.join(cls.CACHE_DIR, "currents", f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_*.pkl")
                    ww3_files = sorted(glob.glob(ww3_pattern), key=os.path.getmtime, reverse=True)
                    curr_files = sorted(glob.glob(curr_pattern), key=os.path.getmtime, reverse=True)
                    
                    if ww3_files and curr_files:
                        ww3_stale, ww3_prov = load_cache_file(ww3_files[0], "INCOIS_WW3", ww3_files[0].split("_cycle_")[-1].replace(".pkl", ""))
                        curr_stale, curr_prov = load_cache_file(curr_files[0], "INCOIS_Currents", curr_files[0].split("_cycle_")[-1].replace(".pkl", ""))
                        
                        if ww3_stale is not None and curr_stale is not None:
                            ww3_prov["stale_fallback"] = True
                            curr_prov["stale_fallback"] = True
                            cls._memory_cache[mem_key] = {"ww3": ww3_stale, "ww3_prov": ww3_prov, "curr": curr_stale, "curr_prov": curr_prov}
                            cls._memory_cache_time[mem_key] = now
                            return ForecastResult(ww3_stale, ww3_prov), ForecastResult(curr_stale, curr_prov)
                raise RuntimeError(f"INCOIS Remote fetch error: {e}") from e"""

content = content.replace(fetch_block, stale_fallback_block)

# Also handle DataUnavailableError and TimeoutError
timeout_block = """            except concurrent.futures.TimeoutError:
                raise TimeoutError("INCOIS OPENDAP remote server timed out.")
            except DataUnavailableError:
                raise
            except Exception as e:"""

timeout_fallback_block = """            except Exception as e:
                if purpose == "visualization":
                    import glob
                    ww3_pattern = os.path.join(cls.CACHE_DIR, "ww3", f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_*.pkl")
                    curr_pattern = os.path.join(cls.CACHE_DIR, "currents", f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_*.pkl")
                    ww3_files = sorted(glob.glob(ww3_pattern), key=os.path.getmtime, reverse=True)
                    curr_files = sorted(glob.glob(curr_pattern), key=os.path.getmtime, reverse=True)
                    
                    if ww3_files and curr_files:
                        # Extract the cycle strings from the filenames
                        try:
                            ww3_stale_cycle = ww3_files[0].split("_cycle_")[-1].replace(".pkl", "")
                            curr_stale_cycle = curr_files[0].split("_cycle_")[-1].replace(".pkl", "")
                            ww3_stale, ww3_prov = load_cache_file(ww3_files[0], "INCOIS_WW3", ww3_stale_cycle)
                            curr_stale, curr_prov = load_cache_file(curr_files[0], "INCOIS_Currents", curr_stale_cycle)
                            
                            if ww3_stale is not None and curr_stale is not None:
                                ww3_prov["stale_fallback"] = True
                                curr_prov["stale_fallback"] = True
                                cls._memory_cache[mem_key] = {"ww3": ww3_stale, "ww3_prov": ww3_prov, "curr": curr_stale, "curr_prov": curr_prov}
                                cls._memory_cache_time[mem_key] = now
                                return ForecastResult(ww3_stale, ww3_prov), ForecastResult(curr_stale, curr_prov)
                        except Exception:
                            pass
                if isinstance(e, concurrent.futures.TimeoutError):
                    raise TimeoutError("INCOIS OPENDAP remote server timed out.")
                if isinstance(e, DataUnavailableError):
                    raise
                raise RuntimeError(f"INCOIS Remote fetch error: {e}") from e"""

content = content.replace(timeout_block, timeout_fallback_block)
# wait, wait I might have replaced `except Exception as e:` twice if it matched. Let's be careful and use start and end indices or `replace_file_content`.
