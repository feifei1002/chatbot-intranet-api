import pytest
from httpx import AsyncClient
from scripts.society_scraping import scrape_links, scrape_content, SocietyModel


@pytest.mark.asyncio
async def test_scrape_links():
    # URL of the website's society index page
    url = "https://www.cardiffstudents.com/activities/societies/"

    # Fetch the live data from the website
    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == 200  # Ensure successful response

        # Parse the HTML content using BeautifulSoup

    # Call the scrape_links function with the parsed HTML
    links = await scrape_links()

    # Validate the structure of the links
    assert isinstance(links, list)  # Ensure links is a list
    # Ensure all elements in links are strings
    assert all(isinstance(link, str) for link in links)


@pytest.mark.asyncio
async def test_scrape_content():
    # Call scrape_links to obtain the URLs
    links = await scrape_links()

    for link in links:

        societies_data = await scrape_content(link)

        # Validate the structure of the societies data
        assert isinstance(societies_data, list)  # Ensure societies_data is a list

        for society in societies_data:
            # Ensure each society is an instance of SocietyModel
            assert isinstance(society, SocietyModel)
