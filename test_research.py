import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.agents.context import AgentContext
from app.agents.research_agent import AcademicResearchAgent
from app.agents.llm_orchestrator import LLMOrchestrator

async def main():
    print("Testing Research Agent...")
    agent = AcademicResearchAgent()
    
    context = AgentContext(
        latitude=19.0760, 
        longitude=72.8777, 
        query="Why has fish productivity declined in the Arabian Sea?",
        mode="fisheries"
    )
    
    result = await agent.analyze(context)
    
    print("\n--- Research Agent Result ---")
    print(f"Status: {result.status}")
    if result.status == "failed":
        print(f"Errors: {result.errors}")
    else:
        for i, paper in enumerate(result.data.get("evidence", [])):
            print(f"\n[{i+1}] {paper['title']}")
            print(f"    Authors: {paper['authors']} | Year: {paper['year']} | OA: {paper['is_oa']}")
            print(f"    Abstract: {paper['abstract'][:100]}...")
            
    print("\n--- Testing LLM Orchestrator Context Resolution ---")
    orchestrator = LLMOrchestrator()
    history = [
        {"role": "user", "content": "Why has fish productivity declined in the Arabian Sea?"},
        {"role": "model", "content": "Recent papers show it is due to algal blooms."}
    ]
    query = "What about the last five years?"
    
    resolved = await orchestrator.resolve_context(query, history)
    print(f"Original: {query}")
    print(f"Resolved: {resolved}")
    
    print("\n--- Testing LLM Follow-Ups ---")
    followups = await orchestrator.generate_followups(resolved, {"agent_results": {"research": result.data}}, history)
    print(f"Follow-ups: {followups}")

if __name__ == "__main__":
    asyncio.run(main())
