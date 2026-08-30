import re
with open("backend/app/main.py", "r") as f:
    content = f.read()

new_startup = """@app.on_event("startup")
def startup_events():
    import threading
    import time
    from datetime import datetime, timezone, timedelta
    from app.db.session import engine, Base
    from app.api.endpoints.safety import get_safety_grid, get_coastal_advisories, get_advisory_animation
    from app.workers.pfz_sync import sync_pfz_advisory

    # Initialize DB schemas
    try:
        Base.metadata.create_all(bind=engine)
        print("Database schemas initialized.")
    except Exception as e:
        print(f"Error initializing DB schemas: {e}")

    def pre_warm_worker():
        print("Pre-warming safety grid and advisories cache in background...")
        try:
            get_coastal_advisories()
            get_advisory_animation()
            print("Advisories cache pre-warming completed!")
        except Exception:
            pass
        for day in [1, 2, 3]:
            for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
                try:
                    get_safety_grid(day, hour)
                except Exception:
                    pass
        print("Safety grid cache pre-warming completed!")

    def pfz_sync_worker_loop():
        # IST is UTC + 5:30
        ist = timezone(timedelta(hours=5, minutes=30))
        print("Starting PFZ synchronization worker daemon...")
        
        # Run immediately on startup once to seed the DB if empty
        try:
            sync_pfz_advisory()
        except Exception as e:
            print(f"Initial PFZ sync failed: {e}")
            
        while True:
            # Check every 30 minutes
            time.sleep(1800)
            now_ist = datetime.now(ist)
            # Only poll INCOIS actively between 17:00 and 21:00 IST
            if 17 <= now_ist.hour <= 21:
                try:
                    sync_pfz_advisory()
                except Exception as e:
                    print(f"PFZ sync failed: {e}")

    threading.Thread(target=pre_warm_worker, daemon=True).start()
    threading.Thread(target=pfz_sync_worker_loop, daemon=True).start()
"""

# Replace the old pre_warm_grid_cache
old_startup_pattern = r'@app\.on_event\("startup"\)\ndef pre_warm_grid_cache\(\):.*?threading\.Thread\(target=worker, daemon=True\)\.start\(\)'
content = re.sub(old_startup_pattern, new_startup, content, flags=re.DOTALL)

with open("backend/app/main.py", "w") as f:
    f.write(content)
