import re

with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

find_str = """    @classmethod
    def clear_caches(cls):
        with cls._lock:
            cls._memory_point_cache.clear()
            cls._memory_geom_cache.clear()
            # Also clear on disk cache for tests
            import shutil
            import glob
            for f in glob.glob(os.path.join(CACHE_DIR, "pt_*")):
                try: os.remove(f)
                except Exception: pass
            for f in glob.glob(os.path.join(CACHE_DIR, "geom_*")):
                try: os.remove(f)
                except Exception: pass"""

replace_str = """    @classmethod
    def clear_caches(cls):
        with cls._lock:
            cls._memory_point_cache.clear()
            cls._memory_geom_cache.clear()
            import shutil
            import glob
            import os
            
            # Clear legacy geometry caches
            for f in glob.glob(os.path.join(CACHE_DIR, "geom_*")):
                try: os.remove(f)
                except Exception: pass
                
            # Clear new sector disk caches
            SECTORS_CACHE_DIR = os.path.join(CACHE_DIR, "sectors")
            if os.path.exists(SECTORS_CACHE_DIR):
                for f in glob.glob(os.path.join(SECTORS_CACHE_DIR, "*.json")):
                    try: os.remove(f)
                    except Exception: pass"""

if find_str in content:
    content = content.replace(find_str, replace_str)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
