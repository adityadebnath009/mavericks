import re

with open("backend/tests/test_pfz_enricher.py", "r") as f:
    content = f.read()

find = '''    @patch("app.api.services.incois_client.incois_client.get")
    def test_cache_thread_safety(mock_get):
        """
        Stress-tests concurrent queries to verify thread safety without race conditions.
        """
        def dummy_get(*args, **kwargs):
            import time
            time.sleep(0.1)
            class DummyResponse:
                content = b'{"status": "success", "value": 28.5}'
                status_code = 200
                def json(self): return {"status": "success", "value": 28.5}
            return DummyResponse()
        mock_get.side_effect = dummy_get'''

replace = '''    @patch("app.api.services.pfz_enricher.PFZEnricherService._resolve_point_metrics")
    def test_cache_thread_safety(mock_resolve):
        """
        Stress-tests concurrent queries to verify thread safety without race conditions.
        """
        def dummy_resolve(*args, **kwargs):
            import time
            time.sleep(0.1)
            return ({"sst": {"value": 28.5}}, "Mock")
        mock_resolve.side_effect = dummy_resolve'''

content = content.replace(find, replace)

with open("backend/tests/test_pfz_enricher.py", "w") as f:
    f.write(content)
