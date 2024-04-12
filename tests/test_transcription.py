from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)


def test_transcription():
    # Checks if .wav file exists.
    file_name = 'tests/gojo.wav'
    assert os.path.exists(file_name), f"File '{file_name}' does not exist."

    # Reads .wav file and stores contents in "audio_blob"
    with open(file_name, 'rb') as file:
        audio_blob = file.read()

    # Tests post request with "audio_blob" as content
    response = client.post(
        "/transcribe",
        content=audio_blob,
        headers={'Content-Type': 'audio/wav'}
    )

    # Tests for successful response
    assert response.status_code == 200
    # Tests for successful transcription
    assert response.json() == {'text': 'domain expansion infinite void'}
