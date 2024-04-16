import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from routes import authentication, deepgram_transcriber
from routes import (chat, suggested_questions, text_to_speech,
                    conversations, admin_analytics, feedback, admin_chat)
from utils import db

OTEL_RESOURCE_ATTRIBUTES = {
    "service.instance.id": str(uuid.uuid1()),
    "environment": "local"
}

# Configure OpenTelemetry to send to an OTLP endpoint
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create(OTEL_RESOURCE_ATTRIBUTES)
    )
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter())
)

HTTPXClientInstrumentor().instrument()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await db.pool.open()
        yield
    finally:
        await db.pool.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(text_to_speech.router)
app.include_router(authentication.router)
app.include_router(suggested_questions.router)
app.include_router(deepgram_transcriber.router)
app.include_router(conversations.router)
app.include_router(feedback.router)
app.include_router(admin_analytics.router)
app.include_router(admin_chat.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


FastAPIInstrumentor().instrument_app(app)
