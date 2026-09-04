from fastapi import APIRouter, HTTPException
import numpy as np

# Import all existing sub-routers
from app.api.endpoints import geofence, safety, vessels, weather, incois_proxy, pfz_router, trip, landing_centers, routing
from app.models import ChatRequest, PipelineResult
from app.agents.planner_agent import PlannerAgent
from app.agents.marine_data_agent import MarineDataDiscoveryAgent
from app.agents.weather_agent import WeatherIntelligenceAgent
from app.agents.ocean_agent import OceanAnalyticsAgent

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

# Initialize the router and the upgraded agent crew
planner = PlannerAgent()
discovery_agent = MarineDataDiscoveryAgent()
weather_agent = WeatherIntelligenceAgent()
ocean_agent = OceanAnalyticsAgent()

@api_router.get("/health")
def health_check():
    return {"status": "ok", "message": "API endpoints are reachable"}

async def run_weather_pipeline(lat: float, lon: float):
    """Fetches live meteorological data and evaluates it against upgraded IMD safety thresholds."""
    met_data = await discovery_agent.fetch_meteorological_data(lat, lon, days=1)
    
    # Automatically utilizes the new IMD color codes and safety scoring
    report = weather_agent.analyze(met_data)
    
    return report.model_dump()

async def run_ocean_pipeline(lat: float, lon: float):
    """Fetches live oceanographic data and identifies PFZs using synthetic spatial gradients."""
    ocean_data = await discovery_agent.fetch_oceanographic_data(lat, lon, days=1)
    
    base_wave = ocean_data.wave_height[0] if ocean_data.wave_height else 0.5
    base_sst = ocean_data.sea_surface_temperature[0] if ocean_data.sea_surface_temperature else 26.0
    
    # UPGRADED: Replaced np.full with the synthetic spatial generator for realistic thermal fronts
    chl_grid, sst_grid, wave_grid = ocean_agent.synthesize_spatial_area(
        base_sst=base_sst, 
        base_wave=base_wave, 
        grid_size=10
    )
    
    # Score fishing grounds using thermal-chlorophyll coincidence edges
    pfz_scores, coincidence, hsi_maps = ocean_agent.score_fishing_grounds(
        chlorophyll_grid=chl_grid, 
        sst_grid=sst_grid, 
        wave_height_grid=wave_grid, 
        time_factor=1.0
    )
    
    return {
        "max_pfz_probability": round(float(np.max(pfz_scores)), 2),
        "coincidence_edge_detected": bool(np.max(coincidence) > 0.0),
        "highly_suitable_species": [
            species for species, grid in hsi_maps.items() if np.max(grid) > 0.8
        ]
    }

@api_router.get("/marine/analyze", response_model=PipelineResult)
async def analyze_marine_conditions(lat: float, lon: float):
    """Runs the parallel data retrieval with latency telemetry."""
    try:
        result = await planner.orchestrate_query(
            weather_func=lambda: run_weather_pipeline(lat, lon),
            ocean_func=lambda: run_ocean_pipeline(lat, lon)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/chat", response_model=PipelineResult)
async def process_chat_query(request: ChatRequest):
    """Processes a natural language query through the upgraded agent crew."""
    try:
        result = await planner.orchestrate_query(
            weather_func=lambda: run_weather_pipeline(request.latitude, request.longitude),
            ocean_func=lambda: run_ocean_pipeline(request.latitude, request.longitude)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))