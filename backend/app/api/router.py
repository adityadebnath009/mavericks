from app.agents.evidence import EvidenceContract, ResultValidator
from fastapi import APIRouter, HTTPException
import numpy as np

# Import all existing sub-routers
from app.api.endpoints import geofence, safety, vessels, weather, incois_proxy, pfz_router, trip, landing_centers, routing, telemetry
from app.models import ChatRequest, PipelineResult
from app.agents.planner_agent import PlannerAgent, AGENT_REGISTRY
from app.agents.context import AgentContext
from app.agents.llm_orchestrator import LLMOrchestrator

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

# Initialize the upgraded agent crew
planner = PlannerAgent()
llm_orchestrator = LLMOrchestrator()

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

@api_router.post("/chat", response_model=PipelineResult)
async def process_chat_query(request: ChatRequest):
    """Processes a natural language query through the full Agentic AI crew (Phase 7)."""
    try:
        # Step 1: Resolve Context
        resolved_query = await llm_orchestrator.resolve_context(request.query, request.history)
        
        # Step 2: Temporal Resolution
        temporal_data = await llm_orchestrator.resolve_temporal_context(resolved_query)
        from app.agents.context import TemporalContext
        temporal_context = TemporalContext(**temporal_data)
        
        # Step 3: LLM determines which agents are required based on user intent
        selected_agents = await llm_orchestrator.determine_agents(resolved_query, AGENT_REGISTRY)
        
        # Ensure fallback payload structure is satisfied for existing frontend
        if "weather" not in selected_agents: selected_agents.append("weather")
        if "ocean" not in selected_agents: selected_agents.append("ocean")
        if "geospatial" not in selected_agents: selected_agents.append("geospatial")

            
        # Generate Evidence Contract
        contract_dict = await llm_orchestrator.generate_evidence_contract(resolved_query)
        contract = EvidenceContract(**contract_dict)
        
        # Step 4: Deterministic DAG execution
        context = AgentContext(
            latitude=request.latitude, 
            longitude=request.longitude, 
            query=resolved_query, 
            mode="fisheries",
            temporal=temporal_context
        )
        dag_result = await planner.orchestrate(context, agents=selected_agents)
        
        # Validate Result against Evidence Contract
        validated_result = ResultValidator.validate(contract, dag_result)
        
        # Step 5: LLM synthesizes the explainable natural language response based on ValidatedResult
        synthesis = await llm_orchestrator.synthesize_response(resolved_query, validated_result, request.history, request.latitude, request.longitude, contract)
        
        dag_result["evidence_contract"] = contract_dict
        dag_result["validation_metrics"] = {
            "evidence": f"{validated_result.met_count}/{validated_result.required_count}",
            "validation": validated_result.validation_status,
            "assessment": validated_result.assessment_status,
            "certification": validated_result.certification_status,
            "confidence": validated_result.confidence,
            "causality": validated_result.causality_status
        }
        
        
        # Step 5: Generate followups
        followups = await llm_orchestrator.generate_followups(resolved_query, dag_result, request.history)
        
        # Attach synthesis and followups to the final payload
        dag_result["conversational_response"] = synthesis
        dag_result["suggested_queries"] = followups
        dag_result["temporal_context"] = temporal_data
        
        return dag_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from app.api.endpoints import research
api_router.include_router(research.router, prefix='/research', tags=['Research'])
