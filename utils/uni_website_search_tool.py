import json
import os
import asyncio

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode, NodeWithScore
from llama_index.postprocessor.cohere_rerank import CohereRerank

from utils.scrape_uni_website import searxng_search, transform_data

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def search_uni_website(query: str) -> str:
    """
    Search the Cardiff University's website for the given query
    """
    search_links = await searxng_search(query)
    documents = await transform_data(search_links)

    # Get the first 10 documents
    nodes = documents[:10]

    # Convert to NodeWithScore
    nodes = [NodeWithScore(node=node) for node in nodes]

    # Reranker
    reranker = CohereRerank(model="rerank-english-v3.0")
    # Reranker asynchronously
    results = await asyncio.to_thread(reranker.postprocess_nodes,
                                      nodes=nodes, query_str=query)
    results = results[:3]

    # return the results in json format to pass to the chat endpoint
    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
