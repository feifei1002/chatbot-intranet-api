from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain.tools import DuckDuckGoSearchResults
from openai import OpenAI
import re

from test import TOGETHER_API_KEY

client = OpenAI(api_key=TOGETHER_API_KEY, base_url="https://api.together.xyz/v1")


def duckduckgo_search(query):
    search = DuckDuckGoSearchResults(source="cardiff.ac.uk")

    # This should take in user input later
    result = search.run(query)

    # get rid of '[' and ']' to extract the link easier
    clean_result = result.replace('[', '').replace(']', '')
    links = re.findall(r'link: (.*?),', clean_result)
    print(links)

    # Uses AsyncHtmlLoader to make asynchronous HTTP requests to fetch the data
    loader = AsyncHtmlLoader(links)
    data = loader.load()

    # Uses HTML2Text to convert HTML content into plain text
    html2text = Html2TextTransformer()
    data_transformed = html2text.transform_documents(data)

    cleanup_document = []
    # Remove all the new line (\n) to clean up
    for doc in data_transformed:
        # cleanup_data = re.compile('\s\s+', doc)
        cleanup_data = doc.page_content.replace(' \n', '').replace('\r', '')
        cleanup_document.append(cleanup_data)
        print(cleanup_data)
        return client.embeddings.create(input=[cleanup_data], model="togethercomputer/m2-bert-80M-32k-retrieval").data[0].embedding
