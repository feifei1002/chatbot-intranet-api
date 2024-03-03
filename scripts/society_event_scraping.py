from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests


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
    title = soup.title.string
    print("Title:", title)


# Call the function to get the links
scraped_links = scrape_links()

# Call the function to scrape content from each link
for link in scraped_links:
    print("Scraping content from:", link)
    scrape_content(link)
