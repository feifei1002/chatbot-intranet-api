import asyncio
import os
import nest_asyncio
from dotenv import load_dotenv
from duckduckgo_search import AsyncDDGS
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_together import TogetherEmbeddings
from langchain_community.llms import Together
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.together import TogetherEmbedding
from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.together import TogetherLLM
from qdrant_client import QdrantClient, AsyncQdrantClient

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
QDRANT_API_KEY = os.environ.get("QDRANT__SERVICE__API_KEY")
QDRANT_URL = os.environ.get("QDRANT_URL")
client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")
embed_model = TogetherEmbedding(
    model_name="togethercomputer/m2-bert-80M-8k-retrieval", api_key=TOGETHER_API_KEY
)

qdrant_client = QdrantClient(QDRANT_URL, api_key=QDRANT_API_KEY)
aclient = AsyncQdrantClient(QDRANT_URL, api_key=QDRANT_API_KEY)
vector_store = QdrantVectorStore(client=qdrant_client, aclient=aclient,
                                 collection_name="uni_web_documents")
llm = TogetherLLM(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1", api_key=TOGETHER_API_KEY
)


async def duckduckgo_search(query):
    # Take in the user's query using Async DuckDuckGoSearch (DDGS)
    async with AsyncDDGS() as addgs:
        # using max_results = 10 to get only the 10 most relevant data
        # and to prevent fetching too much data
        results = [r async for r in addgs.text(query, region='uk-en', safesearch='off',
                                               timelimit='n', backend="api", max_results=3)]

        # Extract the url link from the results
        links = [results['href'] for results in results]
        print(results)
        print(links)
        return links


async def transform_data(links):
    # Uses AsyncHtmlLoader to make asynchronous HTTP requests to fetch the data
    # for link in links:
    loader = AsyncHtmlLoader(links)
    data = loader.load()

    # Create a list to store the transformed data
    data_transformed_list = []
    # Uses HTML2Text to convert HTML content into plain text
    html2text = Html2TextTransformer()
    data_transformed = html2text.transform_documents(data)
    data_transformed[0].page_content = (
        data_transformed[0].page_content.replace(' \n', '').replace('\r', ''))
    # Add the transformed into the list
    data_transformed_list.extend(data_transformed)
    # Split the data into chunks to avoid exceeding tokens limit
    text_splitter = CharacterTextSplitter(
        chunk_size=1024,
        chunk_overlap=20,
        separator="\n"
    )
    documents = text_splitter.split_documents(data_transformed_list)

    return documents


async def main():
    query = "who is the head of school of computer science and informatics for cardiff university?"
    search_links = await duckduckgo_search(query)
    documents = await transform_data(search_links)
    doc = [Document(text=t.page_content) for t in documents]

    splitter = SentenceSplitter(chunk_size=2048, chunk_overlap=50)
    embed_model.embed_batch_size = 50

    pipeline = IngestionPipeline(
        transformations=[
            splitter,
            embed_model
        ],
        vector_store=vector_store
    )

    await pipeline.arun(show_progress=True, documents=doc)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model, use_async=True)
    retriever = index.as_retriever()
    print(retriever)
    results = await retriever.aretrieve("who is the head of school of computer science and informatics for cardiff "
                                        "university?")

    print(results)

    vectorstore = FAISS.from_documents(documents,
                                       TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval"))
    retriever = vectorstore.as_retriever()
    model = Together(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.0,
        max_tokens=1024,
        top_k=50,
    )

    # Provide a template following the LLM's original chat template.
    template = """<s>[INST] Answer the question using only the {context}

    Question: {question} [/INST]
    """
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
    )
    input_query = query
    output = chain.invoke(input_query)

    # This uses TogetherAI model
    print(output)

    # Return value can be change later depends on which one we pass to the chat endpoint
    return output


if __name__ == "__main__":
    load_dotenv()
    nest_asyncio.apply()
    asyncio.run(main())
