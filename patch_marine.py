with open("backend/app/api/services/marine_forecast.py", "r") as f:
    content = f.read()

old_catch = """            except concurrent.futures.TimeoutError:
                logger.warning(f"INCOIS fetch timed out (2s strict limit) for {lat},{lon}")
            except Exception as e:
                logger.warning(f"INCOIS fetch failed for {lat},{lon}, falling back: {e}")"""

new_catch = """            except concurrent.futures.TimeoutError:
                logger.warning(f"INCOIS fetch timed out (2s strict limit) for {lat},{lon}")
                cls._sst_cache[sst_grid_key] = (current_time, sst_value, None)
            except Exception as e:
                logger.warning(f"INCOIS fetch failed for {lat},{lon}, falling back: {e}")
                cls._sst_cache[sst_grid_key] = (current_time, sst_value, None)"""

content = content.replace(old_catch, new_catch)

# Also fix the line where it caches on success to ensure it caches even if chl_value is None, to prevent repeated misses.
old_cache_set = """                if chl_value is not None:
                    cls._sst_cache[sst_grid_key] = (current_time, sst_value, chl_value)"""

new_cache_set = """                cls._sst_cache[sst_grid_key] = (current_time, sst_value, chl_value)"""

content = content.replace(old_cache_set, new_cache_set)

with open("backend/app/api/services/marine_forecast.py", "w") as f:
    f.write(content)
print("patched marine forecast")
