from fastapi.testclient import TestClient
from main import app

# make sure add api key to env variables when running tests
client = TestClient(app)


# basic test for root page
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


# test that /suggested loads with code 200 when no chat history
def test_suggested_questions_no_history():
    response = client.get("/suggested")
    assert response.status_code == 200


# test post request with chat history
def test_post_chat_history():
    response = client.post(
        "/chat_history",
        json={"chat_messages": [{"content": "How old is Cardiff University?"
                                , "role": "user"}]},
    )
    assert response.status_code == 200
