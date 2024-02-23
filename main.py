from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utility.duckduckgo import duckduckgo_search

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chatbot-uni")
async def duckduckgosearch(query: str):
    search_results = await duckduckgo_search(query)
    return {"search_results": search_results}
