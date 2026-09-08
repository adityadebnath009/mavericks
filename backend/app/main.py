import os
import asyncio
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request
from app.core.exceptions import DataUnavailableError, NoSafeRouteError
from app.api.router import api_router
from app.models import ChatRequest, PipelineResult
from app.agents.planner_agent import PlannerAgent
from app.services.cache_updater import periodic_cache_refresh_worker
planner = PlannerAgent()

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

@app.exception_handler(DataUnavailableError)
async def data_unavailable_exception_handler(request: Request, exc: DataUnavailableError):
    return JSONResponse(
        status_code=503,
        content={
            "decision": "DATA_UNAVAILABLE",
            "reason": str(exc),
            "decision_reasons": [{"message": str(exc)}],
            "alternatives": []
        }
    )

@app.exception_handler(NoSafeRouteError)
async def no_safe_route_exception_handler(request: Request, exc: NoSafeRouteError):
    return JSONResponse(
        status_code=200,
        content={"error": "REJECTED_NO_SAFE_ROUTE", "message": str(exc)}
    )

# Register main API routers
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def start_cache_warmer():
    """
    Spawns the background CacheWarmer daemon and starts the coastal advisories worker.
    Initializes Google Earth Engine with Application Default Credentials (ADC).
    """
    import threading
    import ee
    from app.api.services.cache_warmer import cache_warmer

    # Apply IPv4 Global Patch for Urllib3/Requests to fix ISP IPv6 blackholing
    import socket
    _orig_getaddrinfo = socket.getaddrinfo
    def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    socket.getaddrinfo = _ipv4_only_getaddrinfo

    # Initialize Google Earth Engine using ADC (Application Default Credentials)
    try:
        ee.Initialize(project=os.getenv("GOOGLE_CLOUD_PROJECT", "stately-winter-461407-c7"))
        print("[GEE] Successfully initialized Earth Engine with ADC.")
    except Exception as e:
        print(f"[GEE ERROR] Failed to initialize Earth Engine: {e}")

    # Start the robust CacheWarmer
    cache_warmer.start()
    
    # Existing legacy task
    asyncio.create_task(periodic_cache_refresh_worker(interval_hours=5))
    
    # We leave the independent HTML advisories here
    def worker():
        try:
            from app.api.endpoints.safety import get_coastal_advisories, get_advisory_animation
            get_coastal_advisories()
            get_advisory_animation()
            print("Advisories cache pre-warming completed!")
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()

@app.on_event("shutdown")
def stop_cache_warmer():
    from app.api.services.cache_warmer import cache_warmer
    cache_warmer.stop()

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

