from app.agents.user_interaction_agent import UserInteractionAgent

def test_prepare_planner_request():
    agent = UserInteractionAgent()

    intent = agent.extract_intent(
        "Can I go fishing tomorrow morning?"
    )

    request = agent.prepare_planner_request(
        intent,
        user_latitude=21.628,
        user_longitude=87.508,
    )

    assert request == {
        "latitude": 21.628,
        "longitude": 87.508,
        "days": 1,
        "time_factor": 0.25,
    }

def test_explicit_coordinates():
    agent = UserInteractionAgent()

    intent = agent.extract_intent(
        "Is it safe to fish at 21.628, 87.508 tomorrow evening?"
    )

    request = agent.prepare_planner_request(
        intent,
        user_latitude=22.000,
        user_longitude=88.000,
    )

    assert request["latitude"] == 21.628
    assert request["longitude"] == 87.508
    assert request["days"] == 1
    assert request["time_factor"] == 0.75

def main():

    test_prepare_planner_request()
    test_explicit_coordinates()
    print("Planner request tests passed.")

    agent = UserInteractionAgent()

    intent = agent.extract_intent(
        "Can I go fishing tomorrow morning?"
    )

    planner_request = agent.prepare_planner_request(
        intent,
        user_latitude=21.628,
        user_longitude=87.508,
    )

    print("\n" + "=" * 60)
    print("Planner Request Test")
    print(f"Query: Can I go fishing tomorrow morning?")
    print(f"Planner request: {planner_request}")

    intent = agent.extract_intent(
        "Is it safe to fish at 21.628, 87.508 tomorrow evening?"
    )

    planner_request = agent.prepare_planner_request(
        intent,
        user_latitude=22.000,
        user_longitude=88.000,
    )

    print("\n" + "=" * 60)
    print("Explicit Coordinates Test")
    print(f"Query: Is it safe to fish at 21.628, 87.508 tomorrow evening?")
    print(f"Planner request: {planner_request}")

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