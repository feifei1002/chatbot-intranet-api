import json
import os

from llama_index.core import VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding

from utils.scrape_uni_website import duckduckgo_search, transform_data

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def search_uni_website(query: str) -> str:
    """
    Search the Cardiff University's website for the given query
    """
    search_links = await duckduckgo_search(query)
    documents = await transform_data(search_links)
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-large"
    )

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=50)
    pipeline = IngestionPipeline(
        transformations=[
            splitter,
            embed_model,
        ],
        documents=documents,
    )
    nodes = await pipeline.arun(show_progress=True)

    # embed each node
    index = VectorStoreIndex(embed_model=embed_model, nodes=nodes)
    retriever = index.as_retriever(similarity_top_k=3)
    results = await retriever.aretrieve(query)
    print(results)

    # return the results in json format to pass to the chat endpoint
    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
