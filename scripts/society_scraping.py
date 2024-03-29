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


class SocietyModel(BaseModel):
    organisation: str
    content: str
    link: str


async def scrape_links():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.cardiffstudents.com/activities/societies/")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find links using the specified CSS selector
        links = soup.select("li[data-msl-organisation-id] > a.msl-gl-link")

        # Extract href attributes from the links
        href_links = [link['href'] for link in links]

        # Construct absolute URLs
        abs_links = [f"https://www.cardiffstudents.com{href}" for href in href_links]

        return abs_links


async def scrape_content(url):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

    soc_title = soup.find('h1')
    if soc_title:
        society_name = soc_title.get_text(strip=True)
    else:
        society_name = "Society not found or name not available."

    soc_content = soup.select_one("#soc-content")
    if soc_content:
        text_content = soc_content.get_text(separator='\n', strip=True)
    else:
        text_content = "Society content not found."

    # Create SocietyDTO object with society name, content, and link
    society_data = SocietyModel(
        organisation=society_name,
        content=text_content,
        link=url  # Pass the URL as the link field
    )
    # Wrap the society_data in a list before returning
    return society_data


async def main():
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
    results = await retriever.aretrieve("Get me information on the yoga society")

    print(results)


if __name__ == "__main__":
    load_dotenv()

    import nest_asyncio

    nest_asyncio.apply()

    asyncio.run(main())

