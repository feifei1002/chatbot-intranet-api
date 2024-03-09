from httpx import AsyncClient
from ical_library import client as ical_client
from playwright.async_api import async_playwright


async def get_ical_url(cookies_dict: dict) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context()

        page = await context.new_page()

        cookies = []

        for key, value in cookies_dict.items():
            value = value.copy()
            value["name"] = key
            cookies.append(value)

        # Set the cookies
        await context.add_cookies(cookies)

        # Go to the timetable page
        await page.goto("https://timetables.cardiff.ac.uk/")

        # Wait for the page to go to the timetable page
        async with page.expect_navigation(
                url="https://timetables.cardiff.ac.uk/"
        ) as _:
            pass

        # Click on connect calendar button
        await page.click(
            "div.sidebar-content-panel-buttons > div:nth-child(2) > div > button"
        )

        # Click on Other button
        await page.click("div.popupContent > ul > li:nth-child(8) > div")

        # Click on next button
        await page.get_by_text("Next", exact=True).click()

        # Get the ical url from input
        ical_url = await page.locator(
            "input.gwt-TextBox.gwt-TextBox-readonly[type='text']"
        ).input_value()

        return ical_url


async def parse_ical(ical_url: str) -> list[dict]:
    events = []

    async with AsyncClient() as client:
        response = await client.get(ical_url)

        calendar = ical_client.parse_lines_into_calendar(response.text)

        for event in calendar.events:
            events.append({
                "start": event.start.to_datetime_string(),
                "end": event.end.to_datetime_string(),
                "location": event.location.value,
                "description": event.description.value,
            })

    return events
