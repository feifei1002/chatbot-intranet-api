from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)


def test_transcription():

    file_name = '/gojo.wav'
    assert os.path.exists(file_name), f"File '{file_name}' does not exist."

    with open(file_name, 'rb') as file:
        audio_blob = file.read()

    response = client.post(
        "/transcribe",
        data={audio_blob},
        headers={'Content-Type': 'audio/wav'}
    )
    assert response.status_code == 200
    assert response.json() == {'text': 'domain expansion infinite void'}
