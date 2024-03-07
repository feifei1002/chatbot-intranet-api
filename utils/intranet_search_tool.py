import json
import os

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient

# throw Exception if the environment variables are not set
if not os.environ.get("QDRANT_URL"):
    raise ValueError("QDRANT_URL environment variable not set")
if not os.environ.get("QDRANT_API_KEY"):
    raise ValueError("QDRANT_API_KEY environment variable not set")

aclient = AsyncQdrantClient(
    url=os.environ.get("QDRANT_URL"),
    api_key=os.environ.get("QDRANT_API_KEY")
)

store = QdrantVectorStore("intranet", aclient=aclient)

embed_model = OpenAIEmbedding(model="text-embedding-3-large")

index = VectorStoreIndex.from_vector_store(
    vector_store=store,
    embed_model=embed_model,
)


async def search_intranet(query: str) -> str:
    """
    Search the intranet for the given query
    """

    retriever = index.as_retriever(similarity_top_k=3)

    results = await retriever.aretrieve(query)

    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
