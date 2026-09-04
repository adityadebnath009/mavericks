from app.api.services.geospatial_reasoning import GeospatialReasoningService


class GeospatialReasoningAgent:
    """Planner-facing wrapper around GeospatialReasoningService."""

    @staticmethod
    def analyze(lat: float, lon: float) -> dict:
        return GeospatialReasoningService.analyze(lat, lon)


if __name__ == "__main__":
    import json
    result = GeospatialReasoningAgent.analyze(19.8, 85.85)
    print(json.dumps(result, indent=2))
