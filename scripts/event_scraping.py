# Import necessary modules
import asyncio
import os

import httpx  # Async HTTP client library
from bs4 import BeautifulSoup  # Module for web scraping
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
# Base class for creating Pydantic models
from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient


class EventModel(BaseModel):
    date: str
    organisation: str
    name: str
    time: str
    location: str
    description: str


async def scrape_events(soc_event_url):
    # Make an asynchronous HTTP request to fetch the events page
    async with httpx.AsyncClient() as client:
        response = await client.get(soc_event_url)
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

    # Extract event days from the parsed HTML
    event_days = soup.select(".msl_eventlist .eventlist_day")
    events_data = []

    # Iterate over each event day to extract event details
    for day in event_days:
        # Extract the date of the event day
        event_day = day.find("h4").get_text(strip=True)

        # Extract individual events from the event day
        events = day.select(".event_item")

        # Iterate over each event in the event day
        for event_elem in events:
            # Extract event details such as
            # organisation
            # name
            # time
            # location
            # description
            organisation_elem = event_elem.select_one(".msl_event_organisation")
            organisation = organisation_elem.get_text(strip=True) \
                if organisation_elem else "Organisation name not found."
            event_name = event_elem.select_one(
                ".msl_event_name").get_text(strip=True)
            event_time = event_elem.select_one(
                ".msl_event_time").get_text(strip=True)
            event_location = event_elem.select_one(
                ".msl_event_location").get_text(strip=True)
            event_description = event_elem.select_one(
                ".msl_event_description").get_text(strip=True)

            # Handle cases where organisation or description may not be available
            # if not organisation:
            # organisation = "Organisation name not found."

            if not event_description:
                event_description = "Event description not found."

            # Create an EventDTO object with extracted event details
            event_data = EventModel(
                date=event_day,
                organisation=organisation,
                name=event_name,
                time=event_time,
                location=event_location,
                description=event_description
            )
            events_data.append(event_data)

    return events_data


async def main():
    events_result = await scrape_events("https://www.cardiffstudents.com/activities/societies/events/")
    documents = []
    for event in events_result:
        doc = Document(text=event.organisation,
                       metadata={"date": event.date,
                                 "description": event.description,
                                 "name": event.name, "time": event.time,
                                 "location": event.location})
        documents.append(doc)

    # Initialise embedding model
    embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
    embed_model.embed_batch_size = 50

    # Create Qdrant clients
    aclient = AsyncQdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )

    # Create Qdrant vector store
    store = QdrantVectorStore("events", aclient=aclient)

    # Define ingestion pipeline
    pipeline = IngestionPipeline(
        transformations=[splitter, embed_model],
        vector_store=store
    )

    # Ingest documents into Qdrant
    await pipeline.arun(show_progress=True, documents=documents)

    # Create index from vector store
    index = VectorStoreIndex.from_vector_store(vector_store=store,
                                               embed_model=embed_model,
                                               use_async=True)

    # Create retriever from index
    retriever = index.as_retriever(similarity_top_k=3)

    # Perform retrieval query
    results = await retriever.aretrieve("When is the next yoga event?")

    # Print retrieval result
    print(results)

if __name__ == "__main__":
    load_dotenv()

    import nest_asyncio

    nest_asyncio.apply()

    asyncio.run(main())