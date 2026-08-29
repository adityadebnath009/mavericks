from fastapi import APIRouter, HTTPException
import numpy as np

api_router = APIRouter()

from app.api.endpoints import geofence, safety, vessels, weather, incois_proxy, pfz_router
from app.models import ChatRequest, PipelineResult
from app.agents.planner_agent import PlannerAgent
from app.agents.marine_data_agent import MarineDataDiscoveryAgent
from app.agents.weather_agent import WeatherIntelligenceAgent
from app.agents.ocean_agent import OceanAnalyticsAgent

api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(geofence.router, prefix="/geofence", tags=["geofence"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])
api_router.include_router(incois_proxy.router, prefix="/incois", tags=["incois"])
api_router.include_router(pfz_router.router, prefix="/pfz", tags=["pfz"])

# Initialize the router and the agent crew
planner = PlannerAgent()
discovery_agent = MarineDataDiscoveryAgent()
weather_agent = WeatherIntelligenceAgent()
ocean_agent = OceanAnalyticsAgent()


@api_router.get("/health")
def health_check():
    return {"status": "ok", "message": "API endpoints are reachable"}

async def run_weather_pipeline(lat: float, lon: float):
    """Fetches live meteorological data and evaluates it against safety thresholds."""
    # 1. MarineDataDiscoveryAgent handles the API communication
    met_data = await discovery_agent.fetch_meteorological_data(lat, lon, days=1)
    
    # 2. WeatherIntelligenceAgent processes the resulting Python object locally
    report = weather_agent.analyze(met_data)
    
    # Return as a dictionary for the FastAPI response
    return report.model_dump()

async def run_ocean_pipeline(lat: float, lon: float):
    """Fetches live oceanographic data and identifies Potential Fishing Zones."""
    # 1. Fetch live point data
    ocean_data = await discovery_agent.fetch_oceanographic_data(lat, lon, days=1)
    
    # 2. Bridge point data to 2D numpy arrays
    # The Ocean Analytics agent mathematically correlates gradients across spatial grids.
    # Here, we seed a 10x10 synthetic area using the live point data as the baseline.
    base_wave = ocean_data.wave_height[0] if ocean_data.wave_height else 0.5
    base_sst = ocean_data.sea_surface_temperature[0] if ocean_data.sea_surface_temperature else 26.0
    
    waves = np.full((10, 10), base_wave)
    sst = np.full((10, 10), base_sst)
    chlorophyll = np.full((10, 10), 0.2) # Default baseline
    
    # 3. Score the fishing grounds using the advanced numpy math
    pfz_scores, coincidence, hsi_maps = ocean_agent.score_fishing_grounds(
        chlorophyll_grid=chlorophyll, 
        sst_grid=sst, 
        wave_height_grid=waves, 
        time_factor=1.0
    )
    
    # Extract the highest likelihoods to return to the frontend
    return {
        "max_pfz_probability": round(float(np.max(pfz_scores)), 2),
        "coincidence_edge_detected": bool(np.max(coincidence) > 0.0),
        "highly_suitable_species": [
            species for species, grid in hsi_maps.items() if np.max(grid) > 0.8
        ]
    }

@api_router.get("/marine/analyze", response_model=PipelineResult)
async def analyze_marine_conditions(lat: float, lon: float):
    """Runs the parallel data retrieval without conversational parsing."""
    try:
        # Wrap the pipelines in lambdas to pass arguments into the Planner
        result = await planner.orchestrate_query(
            weather_func=lambda: run_weather_pipeline(lat, lon),
            ocean_func=lambda: run_ocean_pipeline(lat, lon)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/chat", response_model=PipelineResult)
async def process_chat_query(request: ChatRequest):
    """Processes a natural language query through the agent crew."""
    try:
        # Pass the coordinates from the ChatRequest payload
        result = await planner.orchestrate_query(
            weather_func=lambda: run_weather_pipeline(request.latitude, request.longitude),
            ocean_func=lambda: run_ocean_pipeline(request.latitude, request.longitude)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))