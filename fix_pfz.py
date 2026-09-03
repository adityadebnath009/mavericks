with open("backend/app/api/services/pfz_enricher.py", "r") as f:
    content = f.read()

content = content.replace(
    'def _resolve_point_metrics(cls, lat: float, lon: float) -> Tuple[Dict[str, Any], str]:',
    'def _resolve_point_metrics(cls, lat: float, lon: float, shutdown_event=None) -> Tuple[Dict[str, Any], str]:'
)

content = content.replace(
    'metrics, source = cls._resolve_point_metrics(lat, lon)',
    'metrics, source = cls._resolve_point_metrics(lat, lon, shutdown_event=shutdown_event)'
)

with open("backend/app/api/services/pfz_enricher.py", "w") as f:
    f.write(content)
