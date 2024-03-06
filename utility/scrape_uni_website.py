import asyncio
import os
import nest_asyncio
from dotenv import load_dotenv
from duckduckgo_search import AsyncDDGS
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from openai import OpenAI
from llama_index.core import VectorStoreIndex, Document
from llama_index.llms.together import TogetherLLM

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
QDRANT_API_KEY = os.environ.get("QDRANT__SERVICE__API_KEY")
QDRANT_URL = os.environ.get("QDRANT_URL")
client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")
llm = TogetherLLM(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1", api_key=TOGETHER_API_KEY
)


async def duckduckgo_search(query):
    # Take in the user's query using Async DuckDuckGoSearch (DDGS)
    async with AsyncDDGS() as addgs:
        # using max_results = 10 to get only the 10 most relevant data
        # and to prevent fetching too much data
        # f"{query} site:cardiff.ac.uk"
        results = [r async for r in addgs.text(f"{query} site:cardiff.ac.uk",
                                               region='uk-en', safesearch='off',
                                               timelimit='n', backend="api", max_results=10)]

        # Extract the url link from the results
        links = [results['href'] for results in results]
        print(results)
        print(links)
        return links


async def transform_data(links):
    # Uses AsyncHtmlLoader to make asynchronous HTTP requests to fetch the data
    loader = AsyncHtmlLoader(links)
    data = loader.load()

    # Uses HTML2Text to convert HTML content into plain text
    html2text = Html2TextTransformer()
    data_transformed = html2text.transform_documents(data)

    # Create a list to store the transformed data
    documents = list(data_transformed)

    return documents


async def main(query):
    # query = "who is the head of school of computer science and informatics?"
    search_links = await duckduckgo_search(query)
    documents = await transform_data(search_links)
    doc = [Document(text=document.page_content) for document in documents]
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-large"
    )

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=50)
    # embed_model.embed_batch_size = 50

    nodes = splitter.get_nodes_from_documents(doc)

    # embed each node
    index = VectorStoreIndex(embed_model=embed_model, nodes=nodes)
    retriever = index.as_retriever()
    # results = await retriever.aretrieve("who is the head of school of "
    #                                     "computer science and informatics?")
    results = await retriever.aretrieve(query)
    print(results)
    return results

    # vectorstore = FAISS.from_documents(documents,
    #                                    TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval"))
    # retriever = vectorstore.as_retriever()
    # model = Together(
    #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    #     temperature=0.0,
    #     max_tokens=1024,
    #     top_k=50,
    # )
    #
    # # Provide a template following the LLM's original chat template.
    # template = """<s>[INST] Answer the question using only the {context}
    #
    # Question: {question} [/INST]
    # """
    # prompt = ChatPromptTemplate.from_template(template)
    #
    # chain = (
    #         {"context": retriever, "question": RunnablePassthrough()}
    #         | prompt
    #         | model
    #         | StrOutputParser()
    # )
    # input_query = query
    # output = chain.invoke(input_query)
    #
    # # This uses TogetherAI model
    # print(output)

    # Return value can be change later depends on which one we pass to the chat endpoint
    # return results


if __name__ == "__main__":
    load_dotenv()
    # https://github.com/run-llama/llama_index/issues/10590#issuecomment-1939298329
    nest_asyncio.apply()
    user_question = "who is the head of school of computer science and informatics?"
    asyncio.run(main(user_question))
