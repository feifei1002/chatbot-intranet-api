import json
import os  # Module for operating system related functionalities

from llama_index.core import Document
from llama_index.core import VectorStoreIndex  # Vector store index from llama_index
# Ingestion pipeline for document processing
from llama_index.core.ingestion import IngestionPipeline
# Sentence splitter for chunking text
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
# Vector store for Qdrant
from llama_index.vector_stores.qdrant import QdrantVectorStore
# Qdrant client for interacting with Qdrant
from qdrant_client import AsyncQdrantClient

from scripts.event_scraping import scrape_events

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def event_scrape_tool(query: str) -> str:
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
                                               embed_model=embed_model)

    # Create retriever from index
    retriever = index.as_retriever(similarity_top_k=3)

    # Perform retrieval query
    results = await retriever.aretrieve(query)

    # Print retrieval result
    print(results)

    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
