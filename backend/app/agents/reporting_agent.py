from app.api.services.reporting import ReportingService


class ReportingAgent:
    """Planner-facing wrapper around ReportingService."""

    @staticmethod
    def compile_report(cause: str = None, risk_factors: dict = None,
                        source_ref: str = None, top_k: int = 3) -> dict:
        return ReportingService.compile_report(
            cause=cause, risk_factors=risk_factors, source_ref=source_ref, top_k=top_k
        )


if __name__ == "__main__":
    import json
    report = ReportingAgent.compile_report(
        cause="Significant Wave Height is predicted to reach 2.9 meters, exceeding your boat's safe limit of 2.5 meters.",
        source_ref="Buoy bay_of_bengal_15n90e",
    )
    print(json.dumps(report, indent=2))
