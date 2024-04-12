from httpx import AsyncClient
from ical_library import client as ical_client
from playwright.async_api import async_playwright
from pydantic import BaseModel

from utils.db import pool


async def get_ical_url(cookies_dict: dict) -> str:
    """
    Fetch the ical url from the timetables service using the cookies
    :param cookies_dict: authentication cookies used to
    browse the timetables service
    :return: the ical url
    """
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


async def get_cached_ical_url(username: str, cookies_dict: dict) -> str:
    """
    Get the cached ical url from the database, else fetch it with
    the cookies and upsert it.
    :param username: the username to lookup in the database for cache
    :param cookies_dict: authentication cookies used to
    fetch ical for timetables service
    :return:
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Check if database has the ical URL already in cache
            await cur.execute(
                "SELECT ical_url FROM ical_cache WHERE username = %s", (username,)
            )

            ical_url = await cur.fetchone()

            if ical_url is None:
                ical_url = await get_ical_url(cookies_dict)
            else:
                return ical_url[0]

            # UPSERT statement to update ical url for user
            await cur.execute(
                "INSERT INTO ical_cache (ical_url, username) VALUES (%s, %s)"
                " ON CONFLICT (username) DO UPDATE SET ical_url = EXCLUDED.ical_url",
                (ical_url, username,)
            )

            return ical_url


class TimetableEvent(BaseModel):
    start: str
    end: str
    location: str
    description: str


async def parse_ical(ical_url: str) -> list[TimetableEvent]:
    """'
    Parse ical url and fetch timetable events from it.

    :param ical_url The ical URL to fetch.
    """
    events = []

    async with AsyncClient() as client:
        response = await client.get(ical_url)

        calendar = ical_client.parse_lines_into_calendar(response.text)

        for event in calendar.events:
            events.append(TimetableEvent(
                start=event.start.to_datetime_string(),
                end=event.end.to_datetime_string(),
                location=event.location.value,
                description=event.description.value,
            ))

    return events
