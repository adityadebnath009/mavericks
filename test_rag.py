import sys
import asyncio
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.api.services.reporting import ReportingService
from app.agents.context import AgentContext
from app.agents.reporting_agent import ReportingAgent

def ingest_mock():
    conn = ReportingService._connect()
    with conn.cursor() as cur:
        # Clear existing
        cur.execute("DELETE FROM marine_safety_corpus;")
        # Insert test
        text = "Under SIH Maritime Safety Code 14.2, vessels under 15 meters must not venture into areas with a significant wave height exceeding 2.5 meters or wind gusts exceeding 40 knots."
        embedding = ReportingService.embed_text(text, task_type="retrieval_document")
        cur.execute(
            """
            INSERT INTO marine_safety_corpus (source, clause_id, text, embedding)
            VALUES (%s, %s, %s, %s);
            """,
            ("SIH Safety Guidelines", "Clause 14.2", text, embedding)
        )
        conn.commit()

async def test_reporting():
    print("Ingesting mock document with Gemini Embeddings...")
    ingest_mock()
    print("Ingestion complete.")
    
    print("\nTesting ReportingAgent (Semantic Search + RAG)...")
    agent = ReportingAgent()
    context = AgentContext(
        latitude=19.0, 
        longitude=72.8,
        query="What are the rules for small vessels in high waves?",
        mode="fisheries"
    )
    context.prior_results = {
        "risk": {
            "primary_hazard": "Significant Wave Height exceeding 2.5 meters",
            "risk_factors": {}
        }
    }
    
    result = await agent.analyze(context)
    print(f"Status: {result.status}")
    if result.status == "success":
        import json
        print(json.dumps(result.data, indent=2))
    else:
        print(f"Errors: {result.errors}")

if __name__ == "__main__":
    asyncio.run(test_reporting())
