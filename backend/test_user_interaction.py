from app.agents.user_interaction_agent import UserInteractionAgent


def main():
    agent = UserInteractionAgent()

    test_queries = [
        "Is it safe to go fishing tomorrow?",
        "How high are the waves today?",
        "Where are the best fishing grounds?",
        "How are the marine conditions today?",
        "Can I travel by boat tomorrow?"
    ]

    for query in test_queries:
        result = agent.extract_intent(query)

        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print(f"Query type: {result.query_type}")
        print(f"Activity type: {result.activity_type}")


if __name__ == "__main__":
    main()