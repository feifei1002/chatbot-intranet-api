import asyncio
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
from qdrant_client import QdrantClient, AsyncQdrantClient

from scripts.society_scraping import scrape_links, scrape_content

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def society_scrape_tool(query: str) -> str:
    # Fetch links asynchronously
    scraped_links = await scrape_links()

    # Asynchronously scrape content from each link
    tasks = [scrape_content(link) for link in scraped_links]
    societies_results = await asyncio.gather(*tasks)

    # Create Document objects for each society
    documents = []
    for society in societies_results:
        doc = Document(
            text=society.organisation,
            metadata={"content": society.content, "URL": society.link}
        )
        documents.append(doc)

    # OpenAI Model works but needs a little tweaking
    embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    splitter = SentenceSplitter(chunk_size=2048, chunk_overlap=20)
    embed_model.embed_batch_size = 50

    aclient = AsyncQdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )

    # Create Qdrant vector store
    store = QdrantVectorStore("societies", aclient=aclient)

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
    results = await retriever.aretrieve(query)

    # Print retrieval result
    print(results)

    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
