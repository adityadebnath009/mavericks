import asyncio
from app.agents.user_interaction_agent import UserInteractionAgent

class MockPlanner:
    async def orchestrate_query(
        self,
        lat,
        lon,
        days=1,
        time_factor=0.5,
    ):
        return {
            "orchestration_status": "success",
            "active_mode": "TEST",
            "received_lat": lat,
            "received_lon": lon,
            "received_days": days,
            "received_time_factor": time_factor,
        }

async def test_execute_planner_request():
    agent = UserInteractionAgent()
    planner = MockPlanner()

    intent = agent.extract_intent(
        "Can I go fishing tomorrow morning?"
    )

    request = agent.prepare_planner_request(
        intent,
        user_latitude=21.628,
        user_longitude=87.508,
    )

    result = await agent.execute_planner_request(
        planner,
        request,
    )

    assert result["orchestration_status"] == "success"
    assert result["received_lat"] == 21.628
    assert result["received_lon"] == 87.508
    assert result["received_days"] == 1
    assert result["received_time_factor"] == 0.25

    print("Planner execution test passed.")
    print(f"Planner received: {result}")

def test_generate_response():

    agent = UserInteractionAgent()

    intent = agent.extract_intent(
        "Is it safe to go fishing tomorrow morning?"
    )

    fake_result = {
        "orchestration_status": "success",
        "active_mode": "TEST",
        "total_latency_ms": 100,
        "is_stale_fallback": True,
        "system_advisory_warning": "Live weather data unavailable; using cached data.",

        "weather_payload": {
            "weather_safety_score": 82,
            "imd_color_code": "GREEN (No Warning)",
            "active_hazards": [],
            "plain_language_summary":
                "Marine weather conditions remain calm and clear."
        },

        "ocean_payload": {
            "average_pfz_score": 0.74
        }
    }

    response = agent.generate_response(
        fake_result,
        intent,
    )

    print("\nGenerated response:")
    print(response)

    assert "⚠️ " in response
    assert "cached data" in response

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

    asyncio.run(test_execute_planner_request())

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

    test_generate_response()

if __name__ == "__main__":
    main()