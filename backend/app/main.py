import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.api.router import api_router

app = FastAPI(
    title="ORCA Marine Portal API",
    description="Backend API for Marine Ecosystem Reasoning, Safety Routing, and Geofencing",
    version="1.0.0",
)

# Set up CORS so the React frontend can fetch data without security errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register main API routers
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def pre_warm_grid_cache():
    """
    Spawns a background task to pre-warm the safety grid cache for all day/hour coordinates.
    """
    import threading
    from app.api.endpoints.safety import get_safety_grid
    
    def worker():
        print("Pre-warming safety grid and advisories cache in background...")
        try:
            from app.api.endpoints.safety import get_coastal_advisories, get_advisory_animation
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

    threading.Thread(target=worker, daemon=True).start()

# Serve React frontend assets statically (Single-Process Local Deployment rule)
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
assets_path = os.path.join(dist_path, "assets")

if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/{fallback_path:path}")
def serve_frontend(fallback_path: str):
    """
    Serves the index.html file for any non-API routes, enabling SPA routing.
    """
    if fallback_path.startswith("api/") or fallback_path == "api":
        return JSONResponse(status_code=404, content={"detail": f"API endpoint /{fallback_path} not found"})
    index_file = os.path.join(dist_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "service": "ORCA Marine Intelligence Portal Backend",
        "version": "1.0.0",
        "note": "Frontend assets not found. Run npm run build in frontend."
    }

