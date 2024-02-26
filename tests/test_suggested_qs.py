from fastapi.testclient import TestClient
from main import app

# make sure add api key to env variables when running tests
client = TestClient(app)


# basic test for root page
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
