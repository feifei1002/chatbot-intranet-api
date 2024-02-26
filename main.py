from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utility.scrapeUniWebsite import duckduckgo_search, transform_data, process_search_results

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chatbot-uni")
async def scrape_uni_website(query):
    search_links = await duckduckgo_search(query)
    transformed_data = transform_data(search_links)
    response = process_search_results(query, search_links)
    return {"response": response}
