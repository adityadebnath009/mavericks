import logging

from fastapi import APIRouter, HTTPException

from app.agents.planner_agent import PlannerAgent
from app.intent import ChatRequest, ChatResponse, ParsedIntent


router = APIRouter()

planner = PlannerAgent()


@router.post("/chat", response_model=ChatResponse)
async def process_chat_query(request: ChatRequest):
    """
    Main entry point for user interactions.

    Flow:
        User input
            ↓
        Intent extraction
            ↓
        Planner Agent
            ↓
        Specialist agents
            ↓
        Human-friendly response
    """

    try:
        # Step 1: Understand the user's request.
        intent = extract_intent_from_text(request.text)

        # Step 2: Determine which coordinates to use.
        lat = request.latitude
        lon = request.longitude

        if lat is None or lon is None:
            raise ValueError(
                "Location coordinates are required to analyze marine conditions."
            )

        # Step 3: Execute the Planner Agent.
        pipeline_results = await planner.orchestrate_query(
            lat=lat,
            lon=lon
        )

        # Step 4: Convert technical results into a user-facing response.
        final_response = generate_regional_explanation(
            results=pipeline_results,
            target_lang=request.language_code
        )

        return ChatResponse(
            spoken_text=final_response,
            extracted_intent=intent,
            pipeline_result=pipeline_results
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:
        logging.exception(
            "User interaction pipeline failed."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to process the marine query."
        )


def extract_intent_from_text(text: str) -> ParsedIntent:
    """
    Temporary intent extraction placeholder.

    This will later be replaced by the actual User Interaction Agent.
    """

    return ParsedIntent(
        activity_type="fishing"
    )


def generate_regional_explanation(
    results: dict,
    target_lang: str
) -> str:
    """
    Temporary response generation logic.

    This will later become part of the User Interaction Agent.
    """

    weather = results.get("weather_payload", {})
    ocean = results.get("ocean_payload", {})

    weather_summary = weather.get(
        "plain_language_summary",
        "Weather information is available."
    )

    pfz_score = ocean.get(
        "average_pfz_score"
    )

    response = weather_summary

    if pfz_score is not None:
        response += (
            f" The current fishing suitability score is "
            f"{round(pfz_score, 2)}."
        )

    return response