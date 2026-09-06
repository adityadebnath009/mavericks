from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from app.api.services.marine_forecast import MarineForecastService
from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile
from app.api.services.pfz_intelligence import PFZIntelligenceService
from app.core.exceptions import DataUnavailableError

router = APIRouter()
logger = logging.getLogger(__name__)

class LocationTelemetryResponse(BaseModel):
    timestamp: str
    lat: float
    lon: float
    marine_severity_score: Optional[float]
    fishing_opportunity_score: Optional[float]
    sst_c: Optional[float]
    chl_mg_m3: Optional[float]
    provenance: dict
    data_status: str

@router.get("/location", response_model=LocationTelemetryResponse)
def get_location_telemetry(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    vessel_length_m: float = Query(10.0, gt=0),
    vessel_beam_m: float = Query(3.0, gt=0),
    vessel_speed_kn: float = Query(10.0, gt=0),
    time: Optional[str] = None
):
    try:
        req_time = datetime.fromisoformat(time.replace('Z', '+00:00')) if time else datetime.utcnow()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid time format")

    try:
        env = MarineForecastService.get_environment(lat, lon, req_time)
        vessel = VesselProfile(length_m=vessel_length_m, beam_m=vessel_beam_m, cruising_speed_kn=vessel_speed_kn)
        
        # Calculate Marine Severity
        engine = OrcaBsiEngine()
        bsi_result = engine.evaluate(env, vessel)
        
        # Calculate Fishing Opportunity
        try:
            fishing_score = PFZIntelligenceService.calculate_fishing_opportunity(env)
        except Exception:
            fishing_score = None

        severity_score = bsi_result["severity_score"]
        
        # If essential data is missing, we must set score to None
        if getattr(env, 'wave_height_m', None) is None or getattr(env, 'wind_speed_kmh', None) is None:
            severity_score = None
            
        prov = getattr(env, 'provenance', {})
        provenance = {
            "sst": {"source": prov.get("sst_c").source if "sst_c" in prov else "missing", "fallback": prov.get("sst_c").fallback if "sst_c" in prov else True},
            "chl": {"source": prov.get("chl_mg_m3").source if "chl_mg_m3" in prov else "missing", "fallback": prov.get("chl_mg_m3").fallback if "chl_mg_m3" in prov else True},
            "wave": {"source": prov.get("wave_height_m").source if "wave_height_m" in prov else "open-meteo"},
            "wind": {"source": prov.get("wind_speed_ms").source if "wind_speed_ms" in prov else "open-meteo"}
        }
        
        return LocationTelemetryResponse(
            timestamp=req_time.isoformat(),
            lat=lat,
            lon=lon,
            marine_severity_score=severity_score,
            fishing_opportunity_score=fishing_score,
            sst_c=env.current.sst_c,
            chl_mg_m3=env.current.chl_mg_m3,
            provenance=provenance,
            data_status="complete" if severity_score is not None and fishing_score is not None else "partial"
        )
    except DataUnavailableError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Telemetry error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
