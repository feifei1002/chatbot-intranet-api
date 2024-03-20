from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_transcription():
    with open('transcription_test.wav', 'rb') as file:
        audio_blob = file.read()

    response = client.post(
        "/transcribe",
        data={audio_blob},
        headers={'Content-Type': 'audio/wav'}
    )

    assert response.status_code == 200
    assert response.json() == {'text': 'domain expansion infinite void'}
