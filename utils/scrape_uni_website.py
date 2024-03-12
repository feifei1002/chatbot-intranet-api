import asyncio
from duckduckgo_search import AsyncDDGS
from functools import partial
from llama_index.readers.web import SimpleWebPageReader


async def duckduckgo_search(query) -> list[str]:
    # using max_results = 10 to get only the 10 most relevant data
    search_function = partial(
        AsyncDDGS().text,
        region='uk-en',
        safesearch='off',
        timelimit='n',
        backend="api",
        max_results=10
    )

    # Take in the user's query using Async DuckDuckGoSearch (DDGS)
    # specify site:cardiff.ac.uk to only search for Cardiff University's website
    async with AsyncDDGS() as addgs:
        results = [r async for r in search_function(f"{query} site:cardiff.ac.uk")]

        # Extract the url link from the results
        links = [results['href'] for results in results]
        print(links)
        return links


def transform_data(links):
    loader = SimpleWebPageReader(html_to_text=True)
    documents = loader.load_data(urls=links)
    return documents


async def main():
    search_links = asyncio.to_thread(duckduckgo_search)
    search_task = asyncio.create_task(search_links)
    await search_task


if __name__ == "__main__":
    asyncio.run(main())
