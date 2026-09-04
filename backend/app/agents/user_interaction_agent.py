from app.intent import ParsedIntent


class UserInteractionAgent:

    def extract_intent(self, text: str) -> ParsedIntent:
        """
        Extract basic user intent using deterministic rules.
        """

        text_lower = text.lower()

        # Default values
        query_type = "marine_overview"
        activity_type = "fishing"

        # Safety-related questions
        safety_keywords = [
            "safe",
            "danger",
            "dangerous",
            "risk",
            "can i go",
            "should i go"
        ]

        # Weather-related questions
        weather_keywords = [
            "weather",
            "wave",
            "wind",
            "rain",
            "storm",
            "temperature"
        ]

        # Fishing-related questions
        fishing_keywords = [
            "fish",
            "fishing",
            "pfz",
            "catch",
            "fishing ground"
        ]

        if any(keyword in text_lower for keyword in safety_keywords):
            query_type = "safety_assessment"

        elif any(keyword in text_lower for keyword in weather_keywords):
            query_type = "weather_conditions"

        elif any(keyword in text_lower for keyword in fishing_keywords):
            query_type = "fishing_conditions"

        # Detect activity
        if "transit" in text_lower or "travel" in text_lower:
            activity_type = "transit"

        elif "dock" in text_lower or "harbor" in text_lower:
            activity_type = "docked"

        return ParsedIntent(
            query_type=query_type,
            activity_type=activity_type
        )