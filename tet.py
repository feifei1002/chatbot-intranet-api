from bs4 import BeautifulSoup
import requests

while True:
    search = input('Search query: ')

    url = f"https://www.cardiffstudents.com/search/?q={search}&section=events%2cgroupings%2cnews%2cresources/"
    req = requests.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    dt_elements = soup.select("#search-results > div.search_groupings > dl > dt")

    club_names = [dt.text.strip() for dt in dt_elements]

    print(club_names)
