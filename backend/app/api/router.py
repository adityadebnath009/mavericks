from fastapi import APIRouter, HTTPException
import numpy as np

# Import all existing sub-routers
from app.api.endpoints import geofence, safety, vessels, weather, incois_proxy, pfz_router, trip, landing_centers, routing, telemetry
from app.models import PipelineResult
from app.agents.planner_agent import PlannerAgent, AGENT_REGISTRY
from app.agents.context import AgentContext

api_router = APIRouter()

# Register all specialized endpoints
api_router.include_router(routing.router, prefix="/routing", tags=["routing"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(geofence.router, prefix="/geofence", tags=["geofence"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])
api_router.include_router(incois_proxy.router, prefix="/incois", tags=["incois"])
api_router.include_router(pfz_router.router, prefix="/pfz", tags=["pfz"])
api_router.include_router(trip.router, prefix="/trip", tags=["trip"])
api_router.include_router(landing_centers.router, prefix="/landing-centers", tags=["landing-centers"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])

# Initialize the legacy agent crew used by established API endpoints.
planner = PlannerAgent()

@api_router.get("/health")
def health_check():
    return {"status": "ok", "message": "API endpoints are reachable"}

@api_router.get("/marine/analyze", response_model=PipelineResult)
async def analyze_marine_conditions(lat: float, lon: float):
    """Runs the orchestrated data retrieval with latency telemetry."""
    try:
        context = AgentContext(latitude=lat, longitude=lon, mode="fisheries")
        # Ensure we run at least the legacy agents to fulfill PipelineResult
        # Risk and reporting will be automatically sorted and executed by Planner
        result = await planner.orchestrate(context, agents=["weather", "ocean", "geospatial", "risk", "reporting"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.api.endpoints import research
api_router.include_router(research.router, prefix='/research', tags=['Research'])
