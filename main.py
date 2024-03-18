from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat, suggested_questions, text_to_speech, store_conversation, conversation_title

from routes import authentication
from utils import db


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
app.include_router(store_conversation.router)
app.include_router(conversation_title.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
