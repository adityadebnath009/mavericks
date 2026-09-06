import re
from typing import Optional, Tuple
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

        latitude, longitude = self.extract_coordinates(text)

        location_name = None

        if latitude is None or longitude is None:
            location_name = self.extract_location_name(text)

        return ParsedIntent(
            query_type=query_type,
            activity_type=activity_type,

            location_name=location_name,

            latitude=latitude,
            longitude=longitude,

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

    def extract_coordinates(
        self,
        text: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract explicit latitude and longitude from user text.

        Expected formats include:
            21.628, 87.508
            21.628 87.508
        """

        coordinate_pattern = re.compile(
            r"(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)"
        )

        match = coordinate_pattern.search(text)

        if not match:
            return None, None

        latitude = float(match.group(1))
        longitude = float(match.group(2))

        # Basic geographic validation.
        if not -90 <= latitude <= 90:
            return None, None

        if not -180 <= longitude <= 180:
            return None, None

        return latitude, longitude

    def extract_location_name(
        self,
        text: str
    ) -> Optional[str]:
        """
        Extract a named location from common natural-language
        location phrases.
        """

        patterns = [
            r"\bnear\s+([A-Za-z][A-Za-z\s-]{1,50})",
            r"\baround\s+([A-Za-z][A-Za-z\s-]{1,50})",
            r"\bat\s+([A-Za-z][A-Za-z\s-]{1,50})",
            r"\bfrom\s+([A-Za-z][A-Za-z\s-]{1,50})",
            r"\bin\s+([A-Za-z][A-Za-z\s-]{1,50})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                location = match.group(1).strip()

                return location.rstrip(".,?!")

        return None

    def resolve_location(
        self,
        intent: ParsedIntent,
        user_latitude: float | None = None,
        user_longitude: float | None = None
    ) -> ParsedIntent:
        """
        Resolve the location using the strongest available source.

        Priority:
            1. Explicit coordinates in the query
            2. Named location
            3. User's current GPS location
        """

        # Explicit coordinates already extracted.
        if intent.latitude is not None and intent.longitude is not None:
            return intent

        # A named location still needs geocoding.
        if intent.location_name:
            return intent

        # Fall back to user's current position.
        if user_latitude is not None and user_longitude is not None:
            intent.latitude = user_latitude
            intent.longitude = user_longitude

        return intent

    def prepare_planner_request(
        self,
        intent: ParsedIntent,
        user_latitude: float | None = None,
        user_longitude: float | None = None,
    ) -> dict:
        """
        Convert a parsed user intent into parameters expected by the Planner Agent.
        """

        # Explicit coordinates from the user's query take priority.
        if intent.latitude is not None and intent.longitude is not None:
            latitude = intent.latitude
            longitude = intent.longitude

        # Otherwise, fall back to the user's current location.
        elif user_latitude is not None and user_longitude is not None:
            latitude = user_latitude
            longitude = user_longitude

        # We cannot ask the Planner for a location we don't have.
        else:
            raise ValueError("No location available for planner request.")

        return {
            "latitude": latitude,
            "longitude": longitude,
            "days": intent.days_ahead,
            "time_factor": intent.time_factor,
        }

    async def execute_planner_request(
        self,
        planner,
        planner_request: dict,
    ) -> dict:
        """
        Execute a prepared request through the Planner Agent.
        """

        return await planner.orchestrate_query(
            planner_request["latitude"],
            planner_request["longitude"],
            days=planner_request["days"],
            time_factor=planner_request["time_factor"],
        )

    
    def generate_response(
        self,
        pipeline_result: dict,
        intent: ParsedIntent,
    ) -> str:
        """
        Convert the Planner result into a human-readable response.
        """
        weather = pipeline_result.get("weather_payload", {})
        ocean = pipeline_result.get("ocean_payload", {})

        response_parts = []

        # ---------------------------------------------------------
        # Data availability / fallback status
        # ---------------------------------------------------------
        warning = pipeline_result.get("system_advisory_warning")
        is_stale_fallback = pipeline_result.get("is_stale_fallback", False)

        if is_stale_fallback:
            if warning:
                response_parts.append(f"⚠️ {warning}")
            else:
                response_parts.append(
                    "⚠️ Live data was unavailable. This assessment is based "
                    "on cached marine intelligence."
                )
        elif warning:
            response_parts.append(f"⚠️ {warning}")

        # ---------------------------------------------------------
        # Weather information
        # ---------------------------------------------------------
        weather_score = weather.get("weather_safety_score")
        imd_code = weather.get("imd_color_code")
        hazards = weather.get("active_hazards", [])

        # ---------------------------------------------------------
        # Intent-specific response
        # ---------------------------------------------------------
        if intent.query_type == "safety_assessment":
            if weather_score is not None:
                response_parts.append(
                    f"Weather safety score: {weather_score}/100."
                )

            if imd_code:
                response_parts.append(
                    f"IMD advisory level: {imd_code}."
                )

            if hazards:
                response_parts.append(
                    f"Active hazards: {', '.join(hazards)}."
                )
            else:
                response_parts.append(
                    "No active weather hazards were detected."
                )

        elif intent.query_type == "weather_conditions":
            summary = weather.get("plain_language_summary")

            if summary:
                response_parts.append(summary)

            if weather_score is not None:
                response_parts.append(
                    f"Weather safety score: {weather_score}/100."
                )

        elif intent.query_type == "fishing_conditions":
            pfz_score = ocean.get("average_pfz_score")

            if pfz_score is not None:
                response_parts.append(
                    f"Average fishing-zone suitability score: "
                    f"{pfz_score:.2f}/1.00."
                )

            if weather_score is not None:
                response_parts.append(
                    f"Weather safety score: {weather_score}/100."
                )

        else:
            summary = weather.get("plain_language_summary")

            if summary:
                response_parts.append(summary)

            pfz_score = ocean.get("average_pfz_score")

            if pfz_score is not None:
                response_parts.append(
                    f"Average fishing-zone suitability score: "
                    f"{pfz_score:.2f}/1.00."
                )

        return " ".join(response_parts)
