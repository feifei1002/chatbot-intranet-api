import os
from deepgram import DeepgramClient, PrerecordedResponse, PrerecordedOptions
from fastapi import APIRouter, Request

router = APIRouter()
deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))


@router.post("/transcribe")
async def transcribe(request: Request):
    data = await request.body()

    source = {
        "buffer": data,
        "mimetype": "audio/ogg"
    }

    resp: PrerecordedResponse = await (deepgram.listen
    .asyncprerecorded.v("1").transcribe_file(
        source,
        PrerecordedOptions(
            model="nova-2"
        ),
    ))

    return {
        "text": resp.results.channels[0].alternatives[0].transcript
    }
