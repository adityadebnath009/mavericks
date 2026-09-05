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

        days_ahead, time_factor = self.extract_time_context(text)

        return ParsedIntent(
            query_type=query_type,
            activity_type=activity_type,
            days_ahead=days_ahead,
            time_factor=time_factor
        )

    def extract_time_context(self, text: str) -> tuple[int, float]:
        """
        Extract basic relative date and time information.

        Returns:
            days_ahead:
                0 = today/current
                1 = tomorrow
                2 = day after tomorrow

            time_factor:
                Approximate fraction of the day.
        """

        text_lower = text.lower()

        days_ahead = 0
        time_factor = 0.5

        # Date extraction
        if "day after tomorrow" in text_lower:
            days_ahead = 2

        elif "tomorrow" in text_lower:
            days_ahead = 1

        # Time extraction
        if "morning" in text_lower:
            time_factor = 0.25

        elif "afternoon" in text_lower:
            time_factor = 0.5

        elif "evening" in text_lower:
            time_factor = 0.75

        elif "night" in text_lower:
            time_factor = 0.9

        return days_ahead, time_factor