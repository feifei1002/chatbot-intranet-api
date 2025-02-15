import asyncio
import os
from typing import Union

import html2text
import httpx
from bs4 import BeautifulSoup
from llama_index.core import Document

client = httpx.AsyncClient()
SEARX_URL = os.getenv("SEARX_URL", "https://searx-api.kavin.rocks")


async def searxng_search(query) -> list[str]:
    print("Searching for:", query)
    # Take in the user's query using SearXNG API
    # specify site:cardiff.ac.uk to only search for Cardiff University's website
    response = await client.get(
        f"{SEARX_URL}/search",
        params={
            "q": f"{query} site:cardiff.ac.uk",
            "format": "json"
        }
    )
    if response.status_code == 200:
        results = response.json().get("results")

        # Extract the url link from the results
        links = [result['url'] for result in results]
        print(links)
        return links


async def get_text(link: str) -> Union[Document, None]:
    """
    Get the text from the given link
    :param link: the link to get the text from
    :return: the markdown text from the link
    """
    try:
        resp = await client.get(link)
        if resp.status_code == 200:
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
        print("Error while parsing the document:", link, e)
        return None


async def transform_data(links):
    tasks = []

    for link in links:
        tasks.append(asyncio.create_task(get_text(link)))
    documents = await asyncio.gather(*tasks)

    # remove None documents
    documents = [doc for doc in documents if doc]

    return documents
