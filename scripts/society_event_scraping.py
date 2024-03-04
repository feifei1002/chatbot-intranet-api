from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from pydantic import BaseModel  # Base class for creating Pydantic models


class SocietyDTO(BaseModel):
    organisation: str
    content: str
    link: str  # Add link field to store the society link


def scrape_links():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://www.cardiffstudents.com/activities/societies/")

    page_source = driver.page_source

    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')

    links = soup.select("#working-on a.msl-gl-link")

    href_links = [f"https://www.cardiffstudents.com{link['href']}" for link in links]

    return href_links


def scrape_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    societies_data = []

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
    society_data = SocietyDTO(
        organisation=society_name,
        content=text_content,
        link=url  # Pass the URL as the link field
    )
    societies_data.append(society_data)

    return societies_data


# Call the function to get the links
scraped_links = scrape_links()

# Call the function to scrape content from each link
for link in scraped_links:
    print("Scraping content from:", link)
    scrape_content(link)
