from openai import OpenAI
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import Response
client = OpenAI()
router = APIRouter()


class TTSRequest(BaseModel):
    text: str


# Pass in the response from the chat endpoint and output it using OpenAI TTS
@router.post("/tts")
async def tts(request: TTSRequest):
    response = client.audio.speech.create(
        model="tts-1",
        input=request.text,
        voice="nova",
        response_format="opus",
    )
    return Response(content=response.content, media_type="audio/ogg")
