import re

with open("backend/tests/test_pfz_enricher.py", "r") as f:
    content = f.read()

find = '''    def test_cache_thread_safety():
        """
        Stress-tests concurrent queries to verify thread safety without race conditions.
        """
        coordinates = ['''

replace = '''    @patch("app.api.services.incois_client.incois_client.get")
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
        mock_get.side_effect = dummy_get
        
        coordinates = ['''

content = content.replace(find, replace)
if "from unittest.mock import patch" not in content:
    content = "from unittest.mock import patch\n" + content

with open("backend/tests/test_pfz_enricher.py", "w") as f:
    f.write(content)
