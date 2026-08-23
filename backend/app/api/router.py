from fastapi import APIRouter

api_router = APIRouter()

# Placeholder route list. In future steps, endpoints will be imported and registered here:
# from app.api.endpoints import weather, routing, geofence, chat
# api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
# api_router.include_router(routing.router, prefix="/routing", tags=["routing"])
# api_router.include_router(geofence.router, prefix="/geofence", tags=["geofence"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

@api_router.get("/health")
def health_check():
    return {"status": "ok", "message": "API endpoints are reachable"}
