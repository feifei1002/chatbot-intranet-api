from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat, suggested_questions

from utility.scrape_uni_website import (duckduckgo_search,
                                        transform_data,
                                        process_search_results)

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
app.include_router(authentication.router)
app.include_router(suggested_questions.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


async def scrape_uni_website(query):
    # get the links for relevant data based on the user's query
    search_links = await duckduckgo_search(query)
    # Transform the data into readable texts
    await transform_data(search_links)
    # Process the data to generate response based on user's query
    response = await process_search_results(query, search_links)
    return {"response": response}
