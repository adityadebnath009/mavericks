from app.agents.user_interaction_agent import UserInteractionAgent


def main():
    agent = UserInteractionAgent()

    test_queries = [
        "Is it safe to go fishing today?",
        "Can I go fishing tomorrow morning?",
        "How are the waves tomorrow evening?",
        "Where should I fish the day after tomorrow?",
        "Is it safe to travel tonight?"
    ]

    for query in test_queries:
        result = agent.extract_intent(query)

        print(f"Query: {query}")
        print(f"Query type: {result.query_type}")
        print(f"Activity type: {result.activity_type}")
        print(f"Days ahead: {result.days_ahead}")
        print(f"Time factor: {result.time_factor}")


if __name__ == "__main__":
    main()