from bs4 import BeautifulSoup
import requests
from pydantic import BaseModel


class SocietyDTO(BaseModel):
    name: str
    content: str


def scrape_society_info(query):
    soc_url = f"https://www.cardiffstudents.com/activities/society/{query}/"
    req = requests.get(soc_url)
    soup = BeautifulSoup(req.content, 'html.parser')

    soc_title = soup.find('h1')

    if soc_title:
        society_name = soc_title.get_text(strip=True)
    else:
        society_name = "Society not found or name not available."

    soc_content = soup.select_one("#soc-content")

    if soc_content:
        text_content = soc_content.get_text(separator='\n', strip=True)
    else:
        text_content = "Society content not found."

    return SocietyDTO(name=society_name, content=text_content)


# Example usage:
while True:
    search_query = input('Search query: ')
    society_info = scrape_society_info(search_query)
    print("Society Name:", society_info.name)
    print("Society Content:", society_info.content)
