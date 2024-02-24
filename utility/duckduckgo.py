import os
import time
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_together import TogetherEmbeddings
from langchain_community.llms import Together
from openai import OpenAI
import re

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")


async def duckduckgo_search(query):
    # wrapper = DuckDuckGoSearchAPIWrapper(max_results=5)
    search = DuckDuckGoSearchResults(source="site:cardiff.ac.uk")

    # This should take in user input later
    result = search.run(query)
    print(result)
    r'(https?://[^\s]+)'

    # get rid of '[' and ']' to extract the link easier
    clean_result = result.replace('[', '').replace('],', '').replace(']', '')
    links = re.findall(r'(https?://[^\s]+)', clean_result)
    print(links)
    data_transformed_list = []
    # Uses AsyncHtmlLoader to make asynchronous HTTP requests to fetch the data
    for link in links:
        loader = AsyncHtmlLoader(link)
        data = loader.load()

        # Uses HTML2Text to convert HTML content into plain text
        html2text = Html2TextTransformer()
        data_transformed = html2text.transform_documents(data)
        print("¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬")
        data_transformed[0].page_content[0:1000].replace(' \n', '').replace('\r', '')
        data_transformed_list.extend(data_transformed)
    vectorstore = FAISS.from_documents(data_transformed_list[:1],
                                       TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval"))
    retriever = vectorstore.as_retriever()
    time.sleep(5)
    model = Together(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.7,
        max_tokens=1024,
        top_k=50,
    )

    # Provide a template following the LLM's original chat template.
    template = """<s>[INST] Answer the question based only on the search:
    {context}

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

    return output
    # found_search = store.similarity_search(
    #     query=query,
    #     k=3,
    # )
    # print("--------------------------")
    # return found_search

        # embeddings_list = []
    # # Remove all the new line (\n) to clean up
    # for doc in data_transformed:
    #     cleanup_data = doc.page_content.replace(' \n', '').replace('\r', '')
    #     print(cleanup_data)
    #     embedding_data = \
    #         client.embeddings.create(input=cleanup_data, model="togethercomputer/m2-bert-80M-32k-retrieval").data[
    #             0].embedding
    #     embeddings_list.append(embedding_data)
    #
    # embedding_query = client.embeddings.create(input=query, model="togethercomputer/m2-bert-80M-32k-retrieval").data[
    #     0].embedding
    # similar_search = []
    # for embedding in embeddings_list:
    #     similarity = cosine_similarity([embedding_query], [embedding])[0][0]
    #     similar_search.append((query, similarity))
    # similar_search.sort(key=lambda x: x[1], reverse=True)
    # recommendations = [search for search, _ in similar_search]
    # print("Recommendations:", recommendations)
    # return recommendations
