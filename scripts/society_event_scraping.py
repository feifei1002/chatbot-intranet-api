from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time


def scrape_links():
    # Launch the Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU usage

    # Launch the Chrome browser with headless options
    driver = webdriver.Chrome(options=chrome_options)

    # Load the webpage
    driver.get("https://www.cardiffstudents.com/activities/societies/")

    # Wait for the dynamic content to load (adjust the sleep time as needed)
    time.sleep(5)  # Wait for 5 seconds

    # Get the page source after the dynamic content has loaded
    page_source = driver.page_source

    # Close the browser
    driver.quit()

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract the desired content
    links = soup.select("#working-on a.msl-gl-link")

    href_links = [link['href'] for link in links]

    print(href_links)


scrape_links()
