import pytest
from httpx import AsyncClient
from scripts.event_scraping import scrape_events, EventModel


@pytest.mark.asyncio
async def event_index_page_test():
    # URL of the website's events index page
    url = "https://www.cardiffstudents.com/activities/societies/events/"

    # Fetch the live data from the website
    async with AsyncClient() as client:
        response = await client.get(url)
        assert response.status_code == 200  # Ensure successful response

    # Call the scrape_events function with the parsed HTML
    events_data = await scrape_events(url)

    # Validate the structure of the events data
    assert isinstance(events_data, list)  # Ensure events_data is a list

    for event in events_data:
        # Ensure each event is an instance of EventModel
        assert isinstance(event, EventModel)
