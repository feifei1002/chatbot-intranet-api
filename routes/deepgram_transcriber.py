import os
from deepgram import DeepgramClient, PrerecordedResponse, PrerecordedOptions
from fastapi import APIRouter, Request

# Initialize the FastAPI router for creating API endpoints
router = APIRouter()
deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))


# Asynchronous endpoint to transcribe audio content.
# Accepts audio data in the request body, sends it to Deepgram for transcription, and returns the transcribed text.
# param "request": The request object containing the body with audio data.
# return: A dictionary with the transcribed text under the key 'text'.
@router.post("/transcribe")
async def transcribe(request: Request):
    data = await request.body()

    # Specifying format and content for transcription
    source = {
        "buffer": data,
        "mimetype": "audio/ogg"
    }

    # Transcribe the audio file using Deepgram's API
    resp: PrerecordedResponse = await (deepgram.listen
    .asyncprerecorded.v("1").transcribe_file(
        source,
        PrerecordedOptions(
            model="nova-2"
        ),
    ))

    # Extract the transcription result from the response
    return {
        "text": resp.results.channels[0].alternatives[0].transcript
    }
