from bs4 import BeautifulSoup
import requests

# Fetch the webpage containing the events
soc_event_url = "https://www.cardiffstudents.com/activities/societies/events/"
req = requests.get(soc_event_url)
soup = BeautifulSoup(req.content, 'html.parser')

# Select all elements with the class "eventlist_day" within the "msl_eventlist" class
event_days = soup.select(".msl_eventlist .eventlist_day")

# Check if there are any event days found
if event_days:
    # Iterate through each event day
    for day in event_days:
        # Extract the text of the h4 tag within the event day, representing the date
        event_day = day.find("h4").get_text(strip=True)
        # Print the date to indicate the events listed are for this day
        print("\nEvents on", event_day)

        # Select all event items within the current event day
        events = day.select(".event_item")
        # Iterate through each event within the current event day
        for event in events:
            # Extract the organization name of the event
            organisation = event.select_one(".msl_event_organisation").get_text(strip=True)
            # Extract the name of the event
            event_name = event.select_one(".msl_event_name").get_text(strip=True)
            # Extract the time of the event
            event_time = event.select_one(".msl_event_time").get_text(strip=True)
            # Extract the location of the event
            event_location = event.select_one(".msl_event_location").get_text(strip=True)

            # Print out the details of the event
            print("Organization:", organisation)
            print("Event Name:", event_name)
            print("Event Time:", event_time)
            print("Event Location:", event_location)
            print("-" * 50)  # Separate each event with dashes
else:
    # If no event days are found, print a message indicating no events were found
    print("No events found.")
