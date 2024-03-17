from contextlib import asynccontextmanager

from honeycomb.opentelemetry import configure_opentelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from honeycomb.opentelemetry import configure_opentelemetry
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from routes import authentication
from routes import chat, suggested_questions, text_to_speech
from utils import db

configure_opentelemetry()
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


@app.get("/")
async def root():
    return {"message": "Hello World"}
