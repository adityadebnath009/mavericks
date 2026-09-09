"""Authenticated GEE evidence for the Intelligence Console only.

Unlike the legacy service's compatibility fallback, this provider never
inventories synthetic SST/chlorophyll values.  It explicitly reports when GEE
is unavailable so the Console can show an honest source state.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from app.api.services.gee_service import GEEService


class GEEIntelligenceProvider:
    @staticmethod
    def _trend(values: list[float]) -> float | None:
        if len(values) < 2:
            return None
        center_x = (len(values) - 1) / 2
        center_y = sum(values) / len(values)
        denominator = sum((index - center_x) ** 2 for index in range(len(values)))
        return sum((index - center_x) * (value - center_y) for index, value in enumerate(values)) / denominator if denominator else None

    @staticmethod
    def _correlation(pairs: list[tuple[float, float]]) -> float | None:
        if len(pairs) < 2:
            return None
        first_mean = sum(first for first, _ in pairs) / len(pairs)
        second_mean = sum(second for _, second in pairs) / len(pairs)
        numerator = sum((first - first_mean) * (second - second_mean) for first, second in pairs)
        first_scale = sum((first - first_mean) ** 2 for first, _ in pairs) ** 0.5
        second_scale = sum((second - second_mean) ** 2 for _, second in pairs) ** 0.5
        return numerator / (first_scale * second_scale) if first_scale and second_scale else None

    @classmethod
    def analyse_annual_series(cls, rows: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Return transparent statistics from authenticated annual rows."""
        sst = [row["sstC"] for row in rows if row.get("sstC") is not None]
        chlorophyll = [row["chlorophyllMgM3"] for row in rows if row.get("chlorophyllMgM3") is not None]
        paired = [(row["sstC"], row["chlorophyllMgM3"]) for row in rows
                  if row.get("sstC") is not None and row.get("chlorophyllMgM3") is not None]
        return {
            "observations": len(rows),
            "sstTrendCPerYear": cls._trend(sst),
            "chlorophyllTrendMgM3PerYear": cls._trend(chlorophyll),
            "sstChlorophyllCorrelation": cls._correlation(paired),
            "pairedObservations": len(paired),
        }

    def historical_annual(self, lat: float, lon: float, years: int = 5) -> Dict[str, Any]:
        if not GEEService.initialize():
            return {"source": "gee", "state": "UNAVAILABLE", "reason": "Earth Engine authentication is unavailable."}
        import ee
        try:
            point = ee.Geometry.Point([lon, lat])
            end_year = datetime.now(timezone.utc).year
            rows = []
            for year in range(end_year - years, end_year):
                start, end = f"{year}-01-01", f"{year + 1}-01-01"
                sst = ee.ImageCollection("NOAA/CDR/OISST/V2_1").filterBounds(point).filterDate(start, end).mean()
                chl = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterBounds(point).select("chlor_a").filterDate(start, end).mean()
                sst_value = sst.reduceRegion(ee.Reducer.mean(), point, 10000).get("sst").getInfo()
                chl_value = chl.reduceRegion(ee.Reducer.mean(), point, 4000).get("chlor_a").getInfo()
                if sst_value is not None or chl_value is not None:
                    rows.append({"year": year, "sstC": float(sst_value) * 0.01 if sst_value is not None else None, "chlorophyllMgM3": float(chl_value) if chl_value is not None else None})
            if not rows:
                return {"source": "gee", "state": "UNAVAILABLE", "reason": "No GEE observations were available for this location/time range."}
            return {"source": "gee", "state": "LIVE", "fetchedAt": datetime.now(timezone.utc).isoformat(),
                    "series": rows, "analysis": self.analyse_annual_series(rows)}
        except Exception as exc:
            return {"source": "gee", "state": "UNAVAILABLE", "reason": str(exc)}
    def current_layers(self) -> Dict[str, Any]:
        if not GEEService.initialize():
            # Preserve the service's disabled layer definitions so the Console
            # legend can state exactly which scientific imagery is unavailable
            # instead of silently showing no layer controls at all.
            return {
                "source": "gee",
                "state": "UNAVAILABLE",
                "reason": "Earth Engine authentication is unavailable.",
                "layers": GEEService.build_overlay_layers(),
            }
        layers = GEEService.build_overlay_layers()
        available = [layer for layer in layers if layer.get("status") == "AVAILABLE"]
        stale = [layer for layer in layers if layer.get("status") == "STALE"]
        return {
            "source": "gee",
            "state": "LIVE" if available else ("STALE" if stale else "UNAVAILABLE"),
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "reason": None if available else ("Earth Engine returned only stale satellite imagery." if stale else "Earth Engine did not create a usable tile layer."),
            "layers": layers,
        }

    def current_ocean_observation(self, lat: float, lon: float) -> Dict[str, Any]:
        if not GEEService.initialize():
            return {"source": "gee", "state": "UNAVAILABLE", "reason": "Earth Engine authentication is unavailable."}
        # Direct authenticated read.  The legacy synthetic fallback is never
        # used by the Intelligence Console.
        import ee
        try:
            point = ee.Geometry.Point([lon, lat])
            sst = ee.ImageCollection("NOAA/CDR/OISST/V2_1").filterBounds(point).sort("system:time_start", False).first()
            chl = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").filterBounds(point).select("chlor_a").sort("system:time_start", False).first()
            sst_value = sst.reduceRegion(ee.Reducer.mean(), point, 10000).get("sst").getInfo()
            chl_value = chl.reduceRegion(ee.Reducer.mean(), point, 4000).get("chlor_a").getInfo()
            return {
                "source": "gee", "state": "LIVE", "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "sstC": float(sst_value) * 0.01 if sst_value is not None else None,
                "chlorophyllMgM3": float(chl_value) if chl_value is not None else None,
            }
        except Exception as exc:
            return {"source": "gee", "state": "UNAVAILABLE", "reason": str(exc)}
