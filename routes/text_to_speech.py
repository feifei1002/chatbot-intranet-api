import time
from openai import OpenAI
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import Response
from opentelemetry import trace
from utils.opentelemetry_setup import setup_opentelemetry

setup_opentelemetry()
client = OpenAI()
router = APIRouter()
tts_tracer = trace.get_tracer("tts_response")


class TTSRequest(BaseModel):
    text: str


# Pass in the response from the chat endpoint and output it using OpenAI TTS
@router.post("/tts")
async def tts(request: TTSRequest):
    with tts_tracer.start_as_current_span("tts_request") as span:
        span.add_event("TTS request started")
        start_time = time.time()
        response = client.audio.speech.create(
            model="tts-1",
            input=request.text,
            voice="nova",
            response_format="opus",
        )
        # Record the end time
        end_time = time.time()

        # Calculate the time taken (milliseconds)
        response_time = int((end_time - start_time) * 1000)

        span.add_event("TTS request completed")
        span.set_attribute("input_text", request.text)
        span.set_attribute("response_time", response_time)
    return Response(content=response.content, media_type="audio/ogg")
