from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

