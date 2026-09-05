from app.agents.user_interaction_agent import UserInteractionAgent


def main():

    agent = UserInteractionAgent()

    test_queries = [
        "What's the weather near me tomorrow?",
        "Is it safe to fish near Digha tomorrow?",
        "Check the conditions around Digha.",
        "Check conditions at 21.628, 87.508.",
        "What are the fishing conditions?"
    ]

    for query in test_queries:

        result = agent.extract_intent(query)

        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print(f"Query type: {result.query_type}")
        print(f"Activity: {result.activity_type}")
        print(f"Location name: {result.location_name}")
        print(f"Latitude: {result.latitude}")
        print(f"Longitude: {result.longitude}")
        print(f"Days ahead: {result.days_ahead}")
        print(f"Time factor: {result.time_factor}")


if __name__ == "__main__":
    main()