from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings

app = FastAPI(
    title="ORCA Marine Portal API",
    description="Backend API for Marine Ecosystem Reasoning, Safety Routing, and Geofencing",
    version="1.0.0"
)

# Set up CORS so the React frontend can fetch data without security errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register main API routers
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "ORCA Marine Intelligence Portal Backend",
        "version": "1.0.0"
    }
