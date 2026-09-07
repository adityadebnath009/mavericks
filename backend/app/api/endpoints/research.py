from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.research_agent import AcademicResearchAgent

router = APIRouter()
agent = AcademicResearchAgent()

class ResearchRequest(BaseModel):
    query: str

@router.post("/query")
async def execute_research_query(req: ResearchRequest):
    try:
        results = await agent.execute_research(req.query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
