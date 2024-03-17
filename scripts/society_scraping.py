import httpx  # Async HTTP client library
from bs4 import BeautifulSoup  # Module for web scraping
# Base class for creating Pydantic models
from pydantic import BaseModel


class SocietyModel(BaseModel):
    organisation: str
    content: str
    link: str


async def scrape_links():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.cardiffstudents.com/activities/societies/")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find links using the specified CSS selector
        links = soup.select("li[data-msl-organisation-id] > a.msl-gl-link")

        # Extract href attributes from the links
        href_links = [link['href'] for link in links]

        # Construct absolute URLs
        abs_links = [f"https://www.cardiffstudents.com{href}" for href in href_links]

        return abs_links


async def scrape_content(url):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

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

    # Create SocietyDTO object with society name, content, and link
    society_data = SocietyModel(
        organisation=society_name,
        content=text_content,
        link=url  # Pass the URL as the link field
    )
    # Wrap the society_data in a list before returning
    return [society_data]
