# app/api/chat.py
from fastapi import APIRouter, HTTPException
from app.intent import ChatRequest, ChatResponse, ParsedIntent
import logging

router = APIRouter()

@router.post("/api/chat", response_model=ChatResponse)
async def process_chat_query(request: ChatRequest):
    """
    Handles the multi-agent pipeline for a single user question.
    """
    try:
        # Step 1: Deterministic Intent Extraction
        # In production, you would use an LLM framework like 'instructor' 
        # to force the LLM to return the ParsedIntent Pydantic model.
        intent = extract_intent_from_text(request.text)
        
        # Step 2: Pass structured data to the Planner Agent
        # The Planner will fan out concurrent tasks to the Weather, Ocean, 
        # and Geospatial agents based on these exact parameters.
        pipeline_results = await planner_agent_execute(
            location=intent.location_name,
            time=intent.departure_time,
            activity=intent.activity_type
        )
        
        # Step 3: Explanation & Translation
        # Synthesize a safe, grounded response in the user's original language.
        final_spoken_text = generate_regional_explanation(
            results=pipeline_results, 
            target_lang=request.language_code
        )
        
        return ChatResponse(
            spoken_text=final_spoken_text,
            risk_score=pipeline_results["final_risk_score"],
            risk_label=pipeline_results["risk_band"],
            extracted_intent=intent
        )

    except Exception as e:
        logging.error(f"Chat pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent pipeline execution failed.")

# --- Mocked internal functions for structural clarity ---

def extract_intent_from_text(text: str) -> ParsedIntent:
    """Mocks the LLM extraction process."""
    return ParsedIntent(
        location_name="Puri Beach",
        activity_type="fishing",
        vessel_size_meters=12.0
    )

async def planner_agent_execute(location, time, activity) -> dict:
    """Mocks the concurrent execution of specialist agents."""
    return {
        "final_risk_score": 25,
        "risk_band": "LOW",
        "evidence": ["Wave height is 1.2m", "No IMD warnings active"]
    }

def generate_regional_explanation(results: dict, target_lang: str) -> str:
    """Mocks the final translation step."""
    return "Sailing tomorrow morning is safe. However, return before 12 PM as wave heights will increase."