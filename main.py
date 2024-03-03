from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat

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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chatbot-uni")
async def scrape_uni_website(query):
    # get the links for relevant data based on the user's query
    search_links = await duckduckgo_search(query)
    # Transform the data into readable texts
    await transform_data(search_links)
    # Process the data to generate response based on user's query
    response = await process_search_results(query, search_links)
    return {"response": response}
