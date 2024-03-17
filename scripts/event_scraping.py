# Import necessary modules

import httpx  # Async HTTP client library
from bs4 import BeautifulSoup  # Module for web scraping
# Base class for creating Pydantic models
from pydantic import BaseModel
# Qdrant client for interacting with Qdrant


class EventModel(BaseModel):
    date: str
    organisation: str
    name: str
    time: str
    location: str
    description: str


async def scrape_events(soc_event_url):
    # Make an asynchronous HTTP request to fetch the events page
    async with httpx.AsyncClient() as client:
        response = await client.get(soc_event_url)
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

    # Extract event days from the parsed HTML
    event_days = soup.select(".msl_eventlist .eventlist_day")
    events_data = []

    # Iterate over each event day to extract event details
    for day in event_days:
        # Extract the date of the event day
        event_day = day.find("h4").get_text(strip=True)

        # Extract individual events from the event day
        events = day.select(".event_item")

        # Iterate over each event in the event day
        for event_elem in events:
            # Extract event details such as
            # organisation
            # name
            # time
            # location
            # description
            organisation_elem = event_elem.select_one(".msl_event_organisation")
            organisation = organisation_elem.get_text(strip=True) \
                if organisation_elem else "Organisation name not found."
            event_name = event_elem.select_one(
                ".msl_event_name").get_text(strip=True)
            event_time = event_elem.select_one(
                ".msl_event_time").get_text(strip=True)
            event_location = event_elem.select_one(
                ".msl_event_location").get_text(strip=True)
            event_description = event_elem.select_one(
                ".msl_event_description").get_text(strip=True)

            # Handle cases where organisation or description may not be available
            # if not organisation:
            # organisation = "Organisation name not found."

            if not event_description:
                event_description = "Event description not found."

            # Create an EventDTO object with extracted event details
            event_data = EventModel(
                date=event_day,
                organisation=organisation,
                name=event_name,
                time=event_time,
                location=event_location,
                description=event_description
            )
            events_data.append(event_data)

    return events_data


