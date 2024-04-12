import asyncio

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

    # Create tasks for scraping content for each link
    tasks = [scrape_content(link) for link in links]

    # Execute tasks concurrently and wait for all to complete
    societies_data_list = await asyncio.gather(*tasks)

    for societies_data in societies_data_list:
        # Validate the structure of the societies data
        assert isinstance(societies_data, list)  # Ensure societies_data is a list

        for society in societies_data:
            # Ensure each society is an instance of SocietyModel
            assert isinstance(society, SocietyModel)


@pytest.mark.asyncio
async def test_search_specific_society_by_link():
    # Define the link of the society to search for
    specific_society_link = "https://www.cardiffstudents.com/activities/society/abbasociety/"

    # Call the scrape_links function with the parsed HTML
    links = await scrape_links()

    # Initialize a variable to track if the specific society is found
    found_society = False

    # Loop through each link to check if it matches the specific link
    for link in links:
        # Check if the link matches the specific society link
        if link == specific_society_link:
            found_society = True
            break

    # Ensure the specific society link is found
    assert found_society, f"Society with link '{specific_society_link}' not found"


@pytest.mark.asyncio
async def test_search_specific_society_by_description():
    # Define the keywords to search for in the society description
    keywords = ["ABBA", "society", "resist"]

    # Call the scrape_links function with the parsed HTML
    soc_links = await scrape_links()

    # Initialize a variable to track if the specific society is found
    found_society_by_description = False

    # Loop through each link to check if any society's description contains the keywords
    for soc_link in soc_links:
        # Call scrape_content for each link to get the description of each society
        society_content = await scrape_content(soc_link)
        for society in society_content:
            # Check if the description contains all the keywords
            if all(keyword in society.content for keyword in keywords):
                found_society_by_description = True
                break

        # Ensure a society with the specific description is found
        assert found_society_by_description, \
            "Society with specified description not found"
