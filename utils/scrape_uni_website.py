import asyncio
from typing import Union

import html2text
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import AsyncDDGS
from llama_index.core import Document

client = httpx.AsyncClient()


async def duckduckgo_search(query) -> list[str]:
    print("Searching for:", query)
    # using max_results = 10 to get only the 10 most relevant data
    # Take in the user's query using Async DuckDuckGoSearch (AsyncDDGS)
    # specify site:cardiff.ac.uk to only search for Cardiff University's website
    async with AsyncDDGS() as addgs:
        results = await addgs.text(
            f"{query} site:cardiff.ac.uk",
            safesearch='off',
            timelimit='n', backend="html",
            max_results=10
        )

        # Extract the url link from the results
        links = [results['href'] for results in results]
        print(links)
        return links


async def get_text(link: str) -> Union[Document, None]:
    """
    Get the text from the given link
    :param link: the link to get the text from
    :return: the markdown text from the link
    """
    resp = await client.get(link)
    if resp.status_code == 200:
        try:
            doc = BeautifulSoup(resp.text, "html.parser")

            # Remove unwanted elements
            for nav in doc.find_all("nav"):
                nav.decompose()
            for footer in doc.find_all("footer"):
                footer.decompose()
            for header in doc.find_all("header"):
                header.decompose()
            for element in doc.recursiveChildGenerator():
                # Skip NavigableString
                if element.name is None:
                    continue

                # Check if element contains these in class
                blacklist = ["footer", "btn"]
                for class_name in element.get("class", []):
                    if class_name in blacklist:
                        element.decompose()
                        break

            # Convert the HTML to markdown
            text = html2text.html2text(str(doc.prettify("utf-8"), encoding='utf-8'))

            return Document(
                text=text,
                extra_info={
                    "Source": link
                }
            )
        except Exception as e:
            print("Error while parsing the document:", e)
            return None


async def transform_data(links):
    tasks = []

    for link in links:
        tasks.append(asyncio.create_task(get_text(link)))
    documents = await asyncio.gather(*tasks)

    # remove None documents
    documents = [doc for doc in documents if doc]

    return documents
