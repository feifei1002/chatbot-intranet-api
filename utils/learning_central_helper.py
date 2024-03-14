import json
import re
from asyncio import sleep
from datetime import datetime
from typing import Optional, Union

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from pydantic import BaseModel

from utils.db import pool

BASE_URL = "https://learningcentral.cf.ac.uk"


async def get_learning_central_cookies(cookies_dict: dict) -> list[dict]:
    """"
    Get the cookies from the learning central service
    :param cookies_dict: authentication cookies used to
    browse the learning central service
    :return: the cookies from the learning central service
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context()

        cookies = []

        for key, value in cookies_dict.items():
            value = value.copy()
            value["name"] = key
            if value["domain"] == ".cf.ac.uk":
                # We change the domain to cardiff.ac.uk
                # Since we're redirected to login.cardiff.ac.uk
                value["domain"] = ".cardiff.ac.uk"
            cookies.append(value)

        # Set the cookies
        await context.add_cookies(cookies)

        block_list = ["timetable", "eesysoft", "aptrinsic", "bluera", "newrelic"]

        # Block certain resources, to speed up the page load
        async def route_intercept(route):
            if route.request.resource_type == "image":
                await route.abort()
            else:
                url = route.request.url
                if any([block in url for block in block_list]):
                    await route.abort()
                else:
                    await route.continue_()

        await context.route("**/*", route_intercept)

        page = await context.new_page()

        # Go to the learning central page
        # Load the profile page since it loads the fastest
        # According to my LightHouse test
        await page.goto("https://learningcentral.cf.ac.uk/ultra/profile")

        # Wait for the page to redirect to Microsoft's
        # "Do you trust this cardiff.ac.uk?"
        await page.wait_for_url("https://login.microsoftonline.com/login.srf")

        # Click on the Continue button
        await page.click("input[value='Continue']")

        # Wait for the page to redirect to the learning central page
        await page.wait_for_url("https://learningcentral.cf.ac.uk/ultra/profile")

        cookies = []

        context_cookies = await context.cookies()

        # Extract the necessary cookies
        for cookie in context_cookies:
            name = cookie["name"]
            names = ["BbRouter", "AWSELB", "AWSELBCORS"]
            if any([name == n for n in names]) or \
                    name == "JSESSIONID" and cookie["path"] == "/learn/api":
                cookies.append({
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                })

        await context.close()

        return cookies


xsrf_matcher = re.compile(
    r"xsrf:([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})"  # noqa matches xsrf:uuid
)
expires_matcher = re.compile(r"expires:(\d+)")  # matches expires:number


async def get_cached_cookies(username: str, cookies_dict: dict) -> list[dict]:
    """
    Get the cached cookies from the database, else fetch it with
    the cookies and upsert it.
    :param username: the username to lookup in the database for cache
    :param cookies_dict: authentication cookies used to
    browse the learning central service
    :return: the cookies from the learning central service
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT cookies FROM learning_central_cookies WHERE username = %s AND"
                " expiry > (select extract(epoch from now()))",
                (username,)
            )
            result = await cur.fetchone()
            if result is not None:
                return json.loads(result[0])
            else:
                cookies = await get_learning_central_cookies(cookies_dict)
                for cookie in cookies:
                    if cookie["name"] == "BbRouter":
                        expiry = int(expires_matcher.search(cookie["value"]).group(1))
                        break
                else:
                    raise Exception("No BbRouter cookie found")
                await cur.execute(
                    "INSERT INTO learning_central_cookies (username, cookies, expiry)"
                    " VALUES (%s, %s, %s)"
                    " ON CONFLICT (username) DO UPDATE"
                    " SET cookies = EXCLUDED.cookies, expiry = EXCLUDED.expiry",
                    (username, json.dumps(cookies), expiry)
                )
                await conn.commit()
                return cookies


def extract_xsrf_value(cookies: list[dict]) -> str:
    """
    Extract the xsrf value from the cookies
    :param cookies: the cookies to extract the xsrf value from
    :return: the xsrf value
    """
    for cookie in cookies:
        if cookie["name"] == "BbRouter":
            return xsrf_matcher.search(cookie["value"]).group(1)
    raise Exception("No BbRouter cookie found")


class GradeDetails(BaseModel):
    course: str
    title: str
    view_url: str
    calculation: str
    score: float
    max_score: float
    display_grade: str


class LearningCentralStreamEntry(BaseModel):
    course: str
    title: str
    view_url: str
    context_extract: Optional[str] = None
    time: str
    content_url: Optional[str] = None
    due_date: Optional[str] = None


async def extract_learning_central_stream_entries(
        cookies: list[dict]
) -> list[Union[LearningCentralStreamEntry, GradeDetails]]:
    """
    Extract the learning central stream entries
    :param cookies: the cookies to use to authenticate
    :return: the stream entries
    """
    xsrf_value = extract_xsrf_value(cookies)

    async with (httpx.AsyncClient() as client):
        # Set the cookies
        for cookie in cookies:
            client.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie["domain"],
                path=cookie["path"]
            )

        # Send initial request to get the providers
        response = await client.post(
            "https://learningcentral.cf.ac.uk/learn/api/v1/streams/ultra", headers={
                "X-Blackboard-Xsrf": xsrf_value,
            }, json={
                "providers": {},
                "forOverview": False,
                "retrieveOnly": False,
                "flushCache": False,
            })

        if response.is_error:
            raise Exception(
                "Failed to get initial learning central data: status "
                f"{response.status_code} data {response.text}"
            )

        data = response.json()

        providers = {}

        # Find and set bb_deployment provider
        for provider in data["sv_providers"]:
            sp_provider = provider["sp_provider"]
            if sp_provider != "bb_deployment":
                continue
            providers[sp_provider] = provider

        # We need to wait, else we don't get all the data
        await sleep(0.5)

        # Send the request to get the stream entries
        response = await client.post(
            "https://learningcentral.cf.ac.uk/learn/api/v1/streams/ultra",
            headers={
                "X-Blackboard-Xsrf": xsrf_value,
            },
            json={
                "providers": providers,
                "forOverview": False,
                "retrieveOnly": True,
                "flushCache": False
            }
        )

        data = response.json()

        # Extract course ids and names
        courses = {}

        for course in data["sv_extras"]["sx_courses"]:
            courses[course["id"]] = course["name"]

        stream_entries = data["sv_streamEntries"]

        if not stream_entries:
            raise Exception("No stream entries found")

        # Raise an exception if we're fetching too quickly
        if data["sv_moreData"]:
            raise Exception("More data found, are we fetching too quickly?")

        # Filter by providerId is bb-nautilus or bb_mygrades
        filter_list = ["bb-nautilus", "bb_mygrades"]
        stream_entries = [
            entry for entry in stream_entries
            if entry["providerId"] in filter_list
        ]

        parsed_entries = []

        # Parse the stream entries
        for entry in stream_entries:
            match entry["providerId"]:
                case "bb-nautilus":
                    # Parse stream entry
                    # Could be an announcement, a due date, or a content item
                    item_specific_data = entry["itemSpecificData"]
                    notification_details = item_specific_data["notificationDetails"]
                    title = item_specific_data["title"]
                    course = courses[notification_details["courseId"]]
                    view_url = BASE_URL + entry['se_itemUri']
                    content_extract = item_specific_data["contentExtract"]
                    if not content_extract:
                        content_extract = None
                    # parse timestamp, and format it to a human-readable format
                    time = datetime.fromtimestamp(
                        entry["se_timestamp"] / 1000
                    ).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    content_url = None

                    # Can be None for announcements
                    if item_specific_data.get("contentDetails"):
                        content_details = item_specific_data["contentDetails"]
                        match content_details.get("contentHandler"):
                            case "resource/x-bb-externallink":
                                content_url = content_details["contentSpecificExtraData"]  # noqa: E501
                            case "resource/x-bb-file":
                                content_url = BASE_URL + \
                                              content_details['contentSpecificFileData']
                            case _:
                                pass

                    # Parse the announcement body
                    announcement_body = notification_details.get("announcementBody")
                    if announcement_body:
                        content_extract = BeautifulSoup(
                            announcement_body,
                            "html.parser"
                        ).get_text(strip=True)

                    # Parse the due date
                    # and convert it to a human-readable format
                    due_date = notification_details.get("dueDate")
                    if due_date:
                        due_date = datetime.strptime(
                            due_date,
                            "%Y-%m-%dT%H:%M:%S.%fZ"
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                    parsed_entries.append(LearningCentralStreamEntry(
                        course=course,
                        title=title,
                        view_url=view_url,
                        context_extract=content_extract,
                        time=time,
                        content_url=content_url,
                        due_date=due_date,
                    ))
                case "bb_mygrades":
                    # Parse the grade details
                    item_specific_data = entry["itemSpecificData"]
                    title = item_specific_data["title"]
                    course = courses[entry["se_courseId"]]
                    view_url = BASE_URL + entry['se_rhs']
                    grade_details = item_specific_data["gradeDetails"]
                    calculation = grade_details["calculationType"]
                    score = grade_details["displayGradeScore"]
                    max_score = grade_details["pointsPossible"]
                    display_grade = grade_details["grade"]
                    parsed_entries.append(GradeDetails(
                        course=course,
                        title=title,
                        view_url=view_url,
                        calculation=calculation,
                        score=score,
                        max_score=max_score,
                        display_grade=display_grade
                    ))

        return parsed_entries
