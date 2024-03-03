from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time


def scrape_links():
    # Set Chrome options to run headlessly
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU usage

    # Launch the Chrome browser with headless options
    driver = webdriver.Chrome(options=chrome_options)  # Make sure chromedriver is in your PATH

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

    # Extract the href attribute from the <a> tag within the #working-on div
    links = soup.select("#working-on a.msl-gl-link")

    href_links = [f"https://www.cardiffstudents.com{link['href']}" for link in links]

    return href_links


# Call the function and print the results
scraped_links = scrape_links()
print(scraped_links)
