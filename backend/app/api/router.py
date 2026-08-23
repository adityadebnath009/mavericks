from fastapi import APIRouter

api_router = APIRouter()

from app.api.endpoints import weather, geofence, safety, vessels

api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(geofence.router, prefix="/geofence", tags=["geofence"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])

@api_router.get("/health")
def health_check():
    return {"status": "ok", "message": "API endpoints are reachable"}
