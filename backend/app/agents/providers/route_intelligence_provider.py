"""Read-only adapter around the established route engine for `/api/chat`.

It never registers a route endpoint or mutates route-engine inputs.  The
Console invokes the existing service only after the user explicitly sets a
destination and separately samples the returned nodes with the Console's
Open-Meteo provider.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.agents.providers.intelligence_marine_provider import IntelligenceMarineProvider
from app.api.services.orca_bsi_engine import VesselProfile
from app.api.services.pfz_routing import PFZRoutingService


class RouteIntelligenceProvider:
    @staticmethod
    def _sample_nodes(path: List[Dict[str, Any]], maximum: int = 5) -> List[Dict[str, Any]]:
        if len(path) <= maximum:
            return path
        indices = sorted({round(index * (len(path) - 1) / (maximum - 1)) for index in range(maximum)})
        return [path[index] for index in indices]

    async def calculate_and_sample(self, origin_lat: float, origin_lon: float, destination_lat: float | None,
                                   destination_lon: float | None) -> Dict[str, Any]:
        if destination_lat is None or destination_lon is None:
            return {"source": "route_engine", "state": "UNAVAILABLE", "reason": "Set a destination on the map before requesting a route."}
        try:
            route = await asyncio.to_thread(
                PFZRoutingService.calculate_optimal_route,
                origin_lat, origin_lon, destination_lat, destination_lon,
                VesselProfile(length_m=8.0, beam_m=2.5, cruising_speed_kn=10.0),
                datetime.now(timezone.utc).isoformat(), False,
            )
        except Exception as exc:
            return {"source": "route_engine", "state": "UNAVAILABLE", "reason": str(exc)}
        if not route or route.get("decision") != "RECOMMENDED" or not route.get("path"):
            return {"source": "route_engine", "state": "UNAVAILABLE", "reason": "The established route engine found no safe route for these points."}

        provider = IntelligenceMarineProvider()
        nodes = self._sample_nodes(route["path"])
        evidence = await asyncio.gather(
            *(provider.collect_safety_evidence(node["lat"], node["lon"], 1) for node in nodes),
            return_exceptions=True,
        )
        samples = []
        for node, node_evidence in zip(nodes, evidence):
            if isinstance(node_evidence, Exception):
                samples.append({"nodeId": node.get("node_id"), "lat": node["lat"], "lon": node["lon"], "state": "UNAVAILABLE", "reason": str(node_evidence)})
                continue
            samples.append({
                "nodeId": node.get("node_id"), "lat": node["lat"], "lon": node["lon"], "eta": node.get("eta"),
                "bsi": node.get("severity_score"), "weather": node_evidence["weather"], "marine": node_evidence["marine"],
            })
        return {"source": "route_engine", "state": "LIVE", "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "route": route, "nodeSamples": samples}
