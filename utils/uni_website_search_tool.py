import json
import os
import asyncio

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode, NodeWithScore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank

from utils.scrape_uni_website import duckduckgo_search, transform_data

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def search_uni_website(query: str) -> str:
    """
    Search the Cardiff University's website for the given query
    """
    search_links = await duckduckgo_search(query)
    documents = await transform_data(search_links)

    # Initialize OpenAI embedding model asynchronously
    await asyncio.create_task(OpenAIEmbedding(model="text-embedding-3-large"))

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=50)
    pipeline = IngestionPipeline(
        transformations=[
            splitter,
        ],
        documents=documents,
    )
    nodes = await pipeline.arun(show_progress=True)[:100]

    # Convert to NodeWithScore
    nodes = [NodeWithScore(node=node) for node in nodes]

    # Initialize the CohereRerank instance
    reranker = CohereRerank()

    # Rerank the nodes asynchronously
    reranked_results = await asyncio.create_task(reranker.postprocess_nodes(nodes=nodes, query_str=query))[:3]

    # return the results in json format to pass to the chat endpoint
    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in reranked_results]
    })
