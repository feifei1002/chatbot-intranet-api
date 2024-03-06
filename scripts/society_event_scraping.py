import asyncio
import os  # Module for operating system related functionalities
import pickle  # Module for serializing and deserializing Python objects
from typing import List, Optional, Any  # Typing module for type hints

import httpx  # Async HTTP client library
import nest_asyncio
from bs4 import BeautifulSoup  # Module for web scraping
from dotenv import load_dotenv  # Module to load environment variables from .env file
from llama_index.core import Document
from llama_index.core import VectorStoreIndex  # Vector store index from llama_index
from llama_index.core.base.embeddings.base import Embedding, BaseEmbedding  # Base classes for embeddings
from llama_index.core.ingestion import IngestionPipeline  # Ingestion pipeline for document processing
from llama_index.core.node_parser import SentenceSplitter  # Sentence splitter for chunking text
from llama_index.vector_stores.qdrant import QdrantVectorStore  # Vector store for Qdrant
from pydantic import BaseModel  # Base class for creating Pydantic models
from pydantic import Field  # Field class from Pydantic for model fields
from qdrant_client import QdrantClient, AsyncQdrantClient  # Qdrant client for interacting with Qdrant
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class SocietyDTO(BaseModel):
    organisation: str
    content: str
    link: str


class CustomTogetherEmbedding(BaseEmbedding):
    api_base: str = Field("https://api.together.xyz/v1", description="Url for Together Embedding API")
    api_key: str = Field("", description="Together API Key")

    def __init__(
            self,
            model_name: str,
            api_key: Optional[str] = None,
            api_base: str = "https://api.together.xyz/v1",
            **kwargs: Any,
    ) -> None:
        api_key = api_key or os.environ.get("TOGETHER_API_KEY", None)
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            api_base=api_base,
            **kwargs,
        )

    def _get_text_embedding(self, text: str) -> Embedding:
        return self._generate_embedding(text, self.model_name)

    def _get_query_embedding(self, query: str) -> Embedding:
        return self._generate_embedding(query, self.model_name)

    async def _agenerate_embedding(self, text: str, model_api_string: str) -> Embedding:
        """Async generate embeddings from Together API.

        Args:
            text: str. An input text sentence or document.
            model_api_string: str. An API string for a specific embedding model of your choice.

        Returns:
            embeddings: a list of float numbers. Embeddings correspond to your given text.
        """
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(
                timeout=None
        ) as client:
            response = await client.post(
                self.api_base.strip("/") + "/embeddings",
                headers=headers,
                json={"input": text, "model": model_api_string},
            )
            if response.status_code != 200:
                raise ValueError(
                    f"Request failed with status code {response.status_code}: {response.text}"
                )

            return response.json()["data"][0]["embedding"]

    def _get_text_embedding(self, text: str) -> Embedding:
        """Get text embedding."""
        return self._generate_embedding(text, self.model_name)

    def _get_query_embedding(self, query: str) -> Embedding:
        """Get query embedding."""
        return self._generate_embedding(query, self.model_name)

    def _get_text_embeddings(self, texts: List[str]) -> List[Embedding]:
        """Get text embeddings."""
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        response = httpx.post(
            self.api_base.strip("/") + "/embeddings",
            headers=headers,
            json={"input": texts, "model": self.model_name},
        )
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )

        return [embedding["embedding"] for embedding in response.json()["data"]]

    async def _aget_text_embedding(self, text: str) -> Embedding:
        """Async get text embedding."""
        return await self._agenerate_embedding(text, self.model_name)

    async def _aget_query_embedding(self, query: str) -> Embedding:
        """Async get query embedding."""
        return await self._agenerate_embedding(query, self.model_name)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[Embedding]:
        """Async get text embeddings."""
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(
                timeout=None
        ) as client:
            response = await client.post(
                self.api_base.strip("/") + "/embeddings",
                headers=headers,
                json={"input": texts, "model": self.model_name},
            )
            if response.status_code != 200:
                raise ValueError(
                    f"Request failed with status code {response.status_code}: {response.text}"
                )

            return [embedding["embedding"] for embedding in response.json()["data"]]


def scrape_links():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://www.cardiffstudents.com/activities/societies/")

    page_source = driver.page_source

    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')

    links = soup.select("#working-on a.msl-gl-link")

    href_links = [f"https://www.cardiffstudents.com{link['href']}" for link in links]

    return href_links


async def scrape_content(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
    societies_data = []

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
    society_data = SocietyDTO(
        organisation=society_name,
        content=text_content,
        link=url  # Pass the URL as the link field
    )
    societies_data.append(society_data)

    return societies_data


async def main():
    # Fetch links asynchronously
    scraped_links = await asyncio.to_thread(scrape_links)

    # Create a list to store the results of scrape_content
    societies_results = []

    # Asynchronously scrape content from each link
    for link in scraped_links:
        # Await the result of scrape_content for each link
        content = await scrape_content(link)
        # Extend the results list with the scraped content
        societies_results.extend(content)

    # Create Document objects for each society
    documents = []
    for society in societies_results:
        # Create Document with text and metadata
        doc = Document(text=society.organisation,
                       metadata={"content": society.content,
                                 "URL": society.link}, )
        documents.append(doc)

    # Save documents to a file
    pickle.dump(documents, open("societies.pkl", "wb"))

    embed_model = CustomTogetherEmbedding(model_name="togethercomputer/m2-bert-80M-2k-retrieval")
    splitter = SentenceSplitter(chunk_size=2048, chunk_overlap=20)
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
    store = QdrantVectorStore("societies", client=client, aclient=aclient)

    # Define ingestion pipeline
    pipeline = IngestionPipeline(
        transformations=[splitter, embed_model],
        vector_store=store
    )

    # Ingest documents into Qdrant
    await pipeline.arun(show_progress=True, documents=documents)

    # Create index from vector store
    index = VectorStoreIndex.from_vector_store(vector_store=store, embed_model=embed_model, use_async=True)

    # Create retriever from index
    retriever = index.as_retriever()

    # Perform retrieval query
    result = await retriever.aretrieve("Give me information on the boxing society")

    # Print retrieval result
    print(result)


# Run the main asynchronous function
if __name__ == "__main__":
    load_dotenv()
    nest_asyncio.apply()
    asyncio.run(main())
