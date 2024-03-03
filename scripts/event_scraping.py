import nest_asyncio
import os
import pickle
import asyncio

from bs4 import BeautifulSoup
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from pydantic import BaseModel

from llama_index.core import Document

from typing import List, Optional, Any

import httpx
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex
from llama_index.core.base.embeddings.base import Embedding, BaseEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.together import TogetherEmbedding

from llama_index.vector_stores.qdrant import QdrantVectorStore

from pydantic import Field
from qdrant_client import QdrantClient, AsyncQdrantClient


class EventDTO(BaseModel):
    date: str
    organisation: str
    name: str
    time: str
    location: str


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


async def scrape_events(soc_event_url):
    async with httpx.AsyncClient() as client:
        response = await client.get(soc_event_url)
        soup = BeautifulSoup(response.text, 'html.parser')

    event_days = soup.select(".msl_eventlist .eventlist_day")
    events_data = []

    for day in event_days:
        event_day = day.find("h4").get_text(strip=True)

        events = day.select(".event_item")

        for event_elem in events:
            organisation = event_elem.select_one(".msl_event_organisation").get_text(strip=True)
            event_name = event_elem.select_one(".msl_event_name").get_text(strip=True)
            event_time = event_elem.select_one(".msl_event_time").get_text(strip=True)
            event_location = event_elem.select_one(".msl_event_location").get_text(strip=True)

            if not organisation:
                organisation = "Unknown"

            event_data = EventDTO(
                date=event_day,
                organisation=organisation,
                name=event_name,
                time=event_time,
                location=event_location
            )
            events_data.append(event_data)

    return events_data


async def main():
    events_result = await scrape_events("https://www.cardiffstudents.com/activities/societies/events/")
    documents = []

    for event in events_result:
        doc = Document(text=event.organisation,
                       metadata={"date": event.date,
                                 "name": event.name, "time": event.time,
                                 "location": event.location})
        documents.append(doc)
        print(doc.get_content(metadata_mode=MetadataMode.EMBED))

    pickle.dump(documents, open("events.pkl", "wb"))

    embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)
    embed_model.embed_batch_size = 50

    client = QdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )
    aclient = AsyncQdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )

    store = QdrantVectorStore("events", client=client, aclient=aclient)
    pipeline = IngestionPipeline(
        transformations=[splitter, embed_model],
        vector_store=store
    )

    await pipeline.arun(show_progress=True, documents=documents)

    index = VectorStoreIndex.from_vector_store(vector_store=store, embed_model=embed_model, use_async=True)

    retriever = index.as_retriever()

    result = await retriever.aretrieve("what gaming events are there?")

    print(result)


if __name__ == "__main__":
    load_dotenv()
    nest_asyncio.apply()

    asyncio.run(main())
