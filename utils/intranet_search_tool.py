import json
import os

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank
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


async def search_intranet(query: str) -> str:
    """
    Search the intranet for the given query
    """

    # Initialize OpenAI embedding model asynchronously
    embed_model = OpenAIEmbedding(model="text-embedding-3-large")

    # Initialize VectorStoreIndex asynchronously
    index = VectorStoreIndex.from_vector_store(
        vector_store=store, embed_model=embed_model)

    # Retrieve top 100 results asynchronously
    retriever = index.as_retriever(similarity_top_k=100)
    results = await retriever.aretrieve(query)

    # Initialize the CohereRerank instance asynchronously
    reranker = CohereRerank()

    # Rerank the results asynchronously
    results = reranker.postprocess_nodes(nodes=results, query_str=query)[:3]

    # More code to allow it to work with Async - Which is also only 2 lines of code.

    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
