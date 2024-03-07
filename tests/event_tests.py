import pytest
from httpx import AsyncClient
from scripts.event_scraping import scrape_events, EventModel

@pytest.mark.asyncio
async def test_event_index_page():
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


@pytest.mark.asyncio
async def test_search_event_and_organisation():
    # URL of the website's events index page
    url = "https://www.cardiffstudents.com/activities/societies/events/"

    # Call the scrape_events function with the parsed HTML
    events_data = await scrape_events(url)

    # Validate the structure of the events data
    assert isinstance(events_data, list)  # Ensure events_data is a list

    # Search for an event name and an organisation name
    event_name_to_search = "Medical Law Panel Event"
    organization_to_search = "Law Society Cardiff"

    found_event = False
    for event in events_data:
        # Check if the event name and organisation name match the search criteria
        if event.name == event_name_to_search and event.organisation == organization_to_search:
            found_event = True
            break

    assert found_event  # Ensure at least one event matches the search criteria
