from llama_index.vector_stores.qdrant import QdrantVectorStore

import qdrant_client

client = qdrant_client.QdrantClient(
    "<qdrant-url>",
    api_key="<qdrant-api-key>", # For Qdrant Cloud, None for local instance
)

vector_store = QdrantVectorStore(client=client, collection_name="documents")
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)