from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat
from utils import text_to_speech

from utility.scrape_uni_website import (duckduckgo_search,
                                        transform_data,
                                        process_search_results)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(text_to_speech.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
