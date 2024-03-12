from duckduckgo_search import AsyncDDGS
from llama_index.readers.web import AsyncWebPageReader


async def duckduckgo_search(query) -> list[str]:
    # using max_results = 10 to get only the 10 most relevant data
    # Take in the user's query using Async DuckDuckGoSearch (AsyncDDGS)
    # specify site:cardiff.ac.uk to only search for Cardiff University's website
    async with AsyncDDGS() as addgs:
        results = [r async for r in addgs.text(f"{query} site:cardiff.ac.uk",
                                               region='uk-en', safesearch='off',
                                               timelimit='n', backend="api",
                                               max_results=10)]

        # Extract the url link from the results
        links = [results['href'] for results in results]
        print(links)
        return links


def transform_data(links):
    loader = AsyncWebPageReader(html_to_text=True)
    documents = loader.load_data(urls=links)
    return documents

