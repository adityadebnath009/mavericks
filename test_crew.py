import sys
import asyncio
import os

# Ensure backend is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.agents.context import AgentContext
from app.agents.planner_agent import PlannerAgent
from app.agents.llm_orchestrator import LLMOrchestrator
from app.agents.planner_agent import AGENT_REGISTRY
from app.config import settings

async def test_all():
    print(f"[*] API Key Loaded: {'Yes' if settings.GEMINI_API_KEY else 'No'}")
    
    planner = PlannerAgent()
    llm = LLMOrchestrator()
    
    test_queries = [
        # Query 1: Safety & RAG focus
        "Is it safe to venture into the sea tomorrow morning near Mumbai?",
        # Query 2: Oceanography & PFZ focus
        "Where is the nearest Potential Fishing Zone today?",
        # Query 3: Pure Regulatory / RAG focus
        "What regulation applies when wave height exceeds my vessel limit?"
    ]
    
    for q in test_queries:
        print(f"\n=======================================================")
        print(f"USER QUERY: {q}")
        print(f"=======================================================")
        
        # 1. LLM Intent Routing
        print("[1] Running LLM Intent Routing...")
        selected_agents = await llm.determine_agents(q, AGENT_REGISTRY)
        print(f"    Selected Agents: {selected_agents}")
        
        # Adding mandatory foundation agents to satisfy standard DAG
        if "weather" not in selected_agents: selected_agents.append("weather")
        if "ocean" not in selected_agents: selected_agents.append("ocean")
            
        # 2. DAG Execution
        print("\n[2] Executing Deterministic DAG...")
        context = AgentContext(
            latitude=19.0760, # Mumbai roughly
            longitude=72.8777,
            query=q,
            mode="fisheries"
        )
        
        dag_result = await planner.orchestrate(context, agents=selected_agents)
        print(f"    Orchestration Status: {dag_result['orchestration_status']}")
        print(f"    Total Latency: {dag_result['total_latency_ms']} ms")
        
        # Inspect RAG specific status
        agent_results = dag_result.get("agent_results", {})
        if "reporting" in agent_results:
            rag = agent_results["reporting"]
            print(f"\n    [RAG CHECK] Reporting Agent Status: {rag.get('status')}")
            if rag.get("status") == "success":
                print(f"    [RAG CHECK] Retrieved Document Count: {len(rag.get('data', {}).get('regulatory_clauses', []))} (Check raw payload if schema differs)")
            else:
                print(f"    [RAG CHECK] Failed/Skipped. Error: {rag.get('errors')}")
        else:
            print(f"\n    [RAG CHECK] Reporting Agent was NOT selected by LLM for this query.")
            
        # 3. LLM Synthesis
        print("\n[3] Synthesizing Final Answer with Gemini 3.5 Flash...")
        synthesis = await llm.synthesize_response(q, dag_result)
        print("\nFINAL RESPONSE:\n")
        print(synthesis)
        print("\n")

if __name__ == "__main__":
    asyncio.run(test_all())
