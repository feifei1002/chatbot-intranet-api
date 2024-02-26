import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_together import TogetherEmbeddings
from langchain_community.llms import Together
from openai import OpenAI
import re

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")
embedding = TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval")


async def duckduckgo_search(query):
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=4, region="uk-en")
    search = DuckDuckGoSearchResults(api_wrapper=wrapper, query=query)

    # This should take in user input later
    result = search.run(query)
    print(result)

    # get rid of '[' and ']' to extract the link easier
    clean_result = result.replace('[', '').replace('],', '').replace(']', '')
    links = re.findall(r'(https?://[^\s]+)', clean_result)
    print(links)

    return links


def transform_data(links):
    # Uses AsyncHtmlLoader to make asynchronous HTTP requests to fetch the data
    # for link in links:
    loader = AsyncHtmlLoader(links)
    data = loader.load()

    # Create a list to store the transformed data
    data_transformed_list = []
    # Uses HTML2Text to convert HTML content into plain text
    html2text = Html2TextTransformer()
    data_transformed = html2text.transform_documents(data)
    data_transformed[0].page_content.replace(' \n', '').replace('\r', '')
    # Add the transformed into the list
    data_transformed_list.extend(data_transformed)
    # Split the data into chunks to avoid exceeding tokens limit
    text_splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0,
        separator="\n"
    )
    documents = text_splitter.split_documents(data_transformed_list)

    return documents


def process_search_results(query, links):

    documents = transform_data(links)
    # Use vectorstore to create embedding for each piece of text
    vectorstore = FAISS.from_documents(documents, TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval"))
    retriever = vectorstore.as_retriever()
    model = Together(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.7,
        max_tokens=1024,
        top_k=50,
    )

    # Provide a template following the LLM's original chat template.
    template = """<s>[INST] Answer the question based on the following {context}

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
    print(output)

    return output
