import asyncio
import os
import pickle
from hashlib import sha256

from dotenv import load_dotenv
from httpx import URL
from llama_index.core import VectorStoreIndex
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.web import WholeSiteReader
from llama_index.vector_stores.qdrant import QdrantVectorStore
from playwright.async_api import async_playwright
from qdrant_client import QdrantClient, AsyncQdrantClient
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class CustomWholeSiteReader(WholeSiteReader):
    # upstream def: def __init__(self, prefix: str, max_depth: int = 10) -> None
    def __init__(self, prefix: str, cookies: dict[str, str], max_depth: int = 10) -> None:  # noqa
        self.cookies = cookies
        self.all_urls = set()
        self.cache = {}
        super().__init__(prefix, max_depth)

    def setup_driver(self):
        """
        Sets up the Selenium WebDriver for Chrome.

        Copied from upstream, with the addition of adding cookies to the driver, and running headless.

        Returns:
            WebDriver: An instance of Chrome WebDriver.
        """  # noqa
        try:
            import chromedriver_autoinstaller
        except ImportError:
            raise ImportError("Please install chromedriver_autoinstaller")

        opt = webdriver.ChromeOptions()
        # opt.add_argument("--start-maximized")
        opt.add_argument("--headless")
        chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=opt)

        driver.get("https://intranet.cardiff.ac.uk/")

        # Add cookies to the driver
        for name, value in self.cookies.items():
            driver.add_cookie({
                "name": name,
                "value": value,
                "domain": ".cardiff.ac.uk"
            })

        return driver

    def cache_path(self, url):
        """
        Find the path of a URL, and cache it.
        :param url: the URL to find the path of
        :return: the path of the URL
        """

        key = sha256(url.encode()).hexdigest()

        if key in self.cache:
            return self.cache[key]

        clean_url = self.clean_url(url)

        url_obj = URL(clean_url)

        path = url_obj.path

        self.cache[key] = path

        return path

    def extract_links(self):
        links = super().extract_links()

        # Hacky logic to remove the link
        # if the same path has been added 10 times already
        # This is done since we had too many search result pages being added

        to_remove = []

        for link in links:

            self.all_urls.add(link)

            count = 0

            url = URL(self.clean_url(link))

            # Ignore links without a query to be fast
            if url.query == "":
                continue

            path = url.path

            for added_url in self.all_urls:
                # find the path of the link
                cur_path = self.cache_path(added_url)
                if path == cur_path:
                    count += 1
                if count > 10:
                    to_remove.append(link)
                    break

        for link in to_remove:
            links.remove(link)

        return links

    def extract_content(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Find intranet content with main.content selector
        try:
            main_content = self.driver.find_element(By.CSS_SELECTOR, "main.content")
            return main_content.text.strip()
        except NoSuchElementException:
            pass

        body_element = self.driver.find_element(By.TAG_NAME, "body")
        return body_element.text.strip()


async def login_browser() -> dict[str, str]:
    """
    Logs into the Cardiff University intranet and returns the cookies
    :return: A dictionary of cookies
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://intranet.cardiff.ac.uk/students")

        # Wait for the intermediate page to load
        async with page.expect_request(
                "https://intranet.cardiff.ac.uk/_saml/saml-account-manager"
        ) as _:
            pass

        # Expect the user to login within 2 minutes
        async with page.expect_navigation(
                url="https://intranet.cardiff.ac.uk/students",
                timeout=120_000
        ) as _:
            print("Please login with your university credentials within 2 minutes")

        cookies = await context.cookies()

        # Find cookie with name "SQ_SYSTEM_SESSION"
        for cookie in cookies:
            name = cookie["name"]
            if name == "SQ_SYSTEM_SESSION":
                return {name: cookie["value"]}

        raise Exception("Cookie not found")


async def main():
    cookies = await login_browser()

    reader = CustomWholeSiteReader(
        "https://intranet.cardiff.ac.uk/students/",
        cookies,
        max_depth=10
    )

    # Scrape the intranet recursively
    documents = reader.load_data("https://intranet.cardiff.ac.uk/students")

    # Dump the documents, in case the script fails later
    pickle.dump(documents, open("intranet.pkl", "wb"))
    # documents = pickle.load(open("intranet.pkl", "rb"))

    # TODO: Created issue upstream for proper batching: https://github.com/run-llama/llama_index/issues/11086
    # We're no longer using Together API for embeddings,
    # as OpenAI's embeddings are more accurate
    # embed_model = TogetherEmbedding(
    #     model_name="togethercomputer/m2-bert-80M-2k-retrieval"
    # )
    embed_model = OpenAIEmbedding(
        model_name="text-embedding-3-large",
    )
    # splitter = SemanticSplitterNodeParser(
    #     buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model
    # )
    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

    embed_model.embed_batch_size = 50

    client = QdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )
    aclient = AsyncQdrantClient(
        url=os.environ.get("QDRANT_URL"),
        api_key=os.environ.get("QDRANT_API_KEY")
    )

    store = QdrantVectorStore("intranet", client=client, aclient=aclient)

    # Create an ingestion pipeline to process the documents
    # First, we split the documents by sentences
    # Then, we embed the sentences using the Together API
    # Finally, we store the embeddings in a vector store
    # The vector store uses Qdrant, a vector database, to store the embeddings
    pipeline = IngestionPipeline(
        transformations=[
            splitter,
            embed_model
        ],
        vector_store=store
    )

    await pipeline.arun(show_progress=True, documents=documents)
    # pipeline.run(show_progress=True, documents=documents)

    index = VectorStoreIndex.from_vector_store(
        vector_store=store,
        embed_model=embed_model,
        use_async=True
    )

    retriever = index.as_retriever()

    # Test the retriever
    result = await retriever.aretrieve(
        "connect to intranet vpn"
    )

    print(result)


if __name__ == "__main__":
    load_dotenv()

    # https://github.com/run-llama/llama_index/issues/10590#issuecomment-1939298329
    import nest_asyncio

    nest_asyncio.apply()

    asyncio.run(main())
