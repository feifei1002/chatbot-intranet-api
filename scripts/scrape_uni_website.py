from duckduckgo_search import AsyncDDGS
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer


async def duckduckgo_search(query):
    # Take in the user's query using Async DuckDuckGoSearch (DDGS)
    async with AsyncDDGS() as addgs:
        # using max_results = 10 to get only the 10 most relevant data
        # and to prevent fetching too much data
        # specify site:cardiff.ac.uk to only search for Cardiff University's website
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
