from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
try:
    response = client.get("/api/incois/pfz-lines")
    print(response.status_code)
    print(response.json())
except Exception as e:
    import traceback
    traceback.print_exc()
