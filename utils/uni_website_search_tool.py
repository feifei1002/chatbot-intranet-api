import os
import json
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.schema import MetadataMode
from scripts.scrape_uni_website import duckduckgo_search, transform_data

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


async def search_uni_website(query: str) -> str:
    """
    Search the Cardiff University's website for the given query
    """
    search_links = await duckduckgo_search(query)
    documents = await transform_data(search_links)
    doc = [Document(text=document.page_content) for document in documents]
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-large"
    )

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=50)

    nodes = splitter.get_nodes_from_documents(doc)

    # embed each node
    index = VectorStoreIndex(embed_model=embed_model, nodes=nodes)
    retriever = index.as_retriever(similarity_top_k=3)
    results = await retriever.aretrieve(query)
    print(results)

    # return the results in json format to pass to the chat endpoint
    return json.dumps({
        "results": [result.get_content(MetadataMode.LLM) for result in results]
    })
