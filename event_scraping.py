import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel


class EventDTO(BaseModel):
    date: str
    organisation: str
    name: str
    time: str
    location: str


def scrape_events():
    soc_event_url = "https://www.cardiffstudents.com/activities/societies/events/"
    req = requests.get(soc_event_url)
    soup = BeautifulSoup(req.content, 'html.parser')

    event_days = soup.select(".msl_eventlist .eventlist_day")
    events_data = []

    for day in event_days:
        # Extract the date of the event day
        event_day = day.find("h4").get_text(strip=True)

        events = day.select(".event_item")

        for event_elem in events:
            organisation = event_elem.select_one(".msl_event_organisation").get_text(strip=True)
            event_name = event_elem.select_one(".msl_event_name").get_text(strip=True)
            event_time = event_elem.select_one(".msl_event_time").get_text(strip=True)
            event_location = event_elem.select_one(".msl_event_location").get_text(strip=True)

            if not organisation:
                organisation = "Unknown"

            # Create an EventDTO object to store event details
            event_data = EventDTO(
                date=event_day,
                organisation=organisation,
                name=event_name,
                time=event_time,
                location=event_location
            )

            # Append event data to the list
            events_data.append(event_data)

    return events_data


events_result = scrape_events()

# Group events by date
events_by_date = {}
for event in events_result:
    date = event.date
    if date not in events_by_date:
        events_by_date[date] = []
    events_by_date[date].append(event)

# Print events grouped by date
for date, events_list in events_by_date.items():
    print("\nEvents on", date, "\n")
    for event in events_list:
        print("Organization:", event.organisation)
        print("Event Name:", event.name)
        print("Event Time:", event.time)
        print("Event Location:", event.location)
        print("-" * 50)
