from bs4 import BeautifulSoup
import requests

while True:
    search = input('Search query: ')

    soc_url = f"https://www.cardiffstudents.com/activities/society/{search}/"
    req = requests.get(soc_url)
    soup = BeautifulSoup(req.content, 'html.parser')

    soc_title = soup.find('h1')

    if soc_title:
        society_name = soc_title.get_text(strip=True)
        print("Society Name:", society_name)
    else:
        print("Society not found or name not available.")

    soc_content = soup.select_one("#soc-content")

    if soc_content:
        text_content = soc_content.get_text(separator='\n', strip=True)
        print("Society Content:", text_content)
    else:
        print("Society content not found.")
