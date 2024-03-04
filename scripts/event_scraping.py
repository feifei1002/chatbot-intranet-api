# Import necessary modules
import asyncio  # Module for writing asynchronous code
import os  # Module for operating system related functionalities
import pickle  # Module for serializing and deserializing Python objects

import httpx  # Async HTTP client library
import nest_asyncio  # Module to enable nested asyncio event loops
from bs4 import BeautifulSoup  # Module for web scraping
from dotenv import load_dotenv  # Module to load environment variables from .env file
from llama_index.core import Document  # Document class from llama_index
from llama_index.core import VectorStoreIndex  # Vector store index from llama_index
from llama_index.core.ingestion import IngestionPipeline  # Ingestion pipeline for document processing
from llama_index.core.node_parser import SentenceSplitter  # Sentence splitter for chunking text
from llama_index.core.schema import MetadataMode  # Metadata mode enum from llama_index
from llama_index.embeddings.openai import OpenAIEmbedding  # OpenAI embedding model
from llama_index.vector_stores.qdrant import QdrantVectorStore  # Vector store for Qdrant
from pydantic import BaseModel  # Base class for creating Pydantic models
from qdrant_client import QdrantClient, AsyncQdrantClient  # Qdrant client for interacting with Qdrant


class EventDTO(BaseModel):
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
            # Extract event details such as organisation, name, time, location, and description
            organisation = event_elem.select_one(".msl_event_organisation").get_text(strip=True)
            event_name = event_elem.select_one(".msl_event_name").get_text(strip=True)
            event_time = event_elem.select_one(".msl_event_time").get_text(strip=True)
            event_location = event_elem.select_one(".msl_event_location").get_text(strip=True)
            event_description = event_elem.select_one(".msl_event_description").get_text(strip=True)

            # Handle cases where organisation or description may not be available
            if not organisation:
                organisation = "Organisation name not found."

            if not event_description:
                event_description = "Event description not found."

            # Create an EventDTO object with extracted event details
            event_data = EventDTO(
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
    # Scrape events data
    events_result = await scrape_events("https://www.cardiffstudents.com/activities/societies/events/")

    # Create Document objects for each event
    documents = []
    for event in events_result:
        # Create Document with text and metadata
        doc = Document(text=event.organisation,
                       metadata={"date": event.date,
                                 "description": event.description,
                                 "name": event.name, "time": event.time,
                                 "location": event.location})
        documents.append(doc)

        # Print content with metadata for each document
        print(doc.get_content(metadata_mode=MetadataMode.EMBED))

    # Save documents to a file
    pickle.dump(documents, open("events.pkl", "wb"))

    # Initialise embedding model
    embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
    embed_model.embed_batch_size = 50

    # Create Qdrant clients
    client = QdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )
    aclient = AsyncQdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )

    # Create Qdrant vector store
    store = QdrantVectorStore("events", client=client, aclient=aclient)

    # Define ingestion pipeline
    pipeline = IngestionPipeline(
        transformations=[splitter, embed_model],
        vector_store=store
    )

    # Ingest documents into Qdrant
    await pipeline.arun(show_progress=True, documents=documents)

    # Create index from vector store
    index = VectorStoreIndex.from_vector_store( vector_store=store, embed_model=embed_model, use_async=True)

    # Create retriever from index
    retriever = index.as_retriever()

    # Perform retrieval query
    result = await retriever.aretrieve("what gaming events are there?")

    # Print retrieval result
    print(result)


# Check if the script is being run as the main module
if __name__ == "__main__":
    # Load environment variables from the .env file
    load_dotenv()

    # Enable nested asyncio event loops
    nest_asyncio.apply()

    # Run the main asynchronous function
    asyncio.run(main())
