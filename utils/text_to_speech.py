from fastapi.openapi.models import Response
from openai import OpenAI
from pydantic import BaseModel
from fastapi import FastAPI, APIRouter
from fastapi.responses import Response

app = FastAPI()
client = OpenAI()
router = APIRouter()


class TTSRequest(BaseModel):
    text: str


@router.post("/tts")
async def tts(request: TTSRequest):
    resp = client.audio.speech.create(
        model="tts-1",
        input=request.text,
        voice="nova",
        response_format="opus",
    )

    return Response(content=resp.content, media_type="audio/ogg")
