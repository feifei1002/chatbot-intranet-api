from playwright.async_api import async_playwright, TimeoutError
from pydantic import BaseModel


class UniCredentials(BaseModel):
    username: str
    password: str


class BadCredentialsException(Exception):
    pass


async def login(credentials: UniCredentials):
    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context()

        page = await context.new_page()

        await page.goto("https://intranet.cardiff.ac.uk/students")

        # Wait for redirect to login page
        async with page.expect_navigation(
                url="https://login.cardiff.ac.uk/nidp/idff/sso"
        ) as _:
            pass

        # Fill in the username and password
        await page.fill("#username", credentials.username)
        await page.fill("#Ecom_Password", credentials.password)

        # Click the login button
        await page.click("#login-form > fieldset > input[type='submit']")

        # Wait until page finishes loading
        await page.wait_for_load_state("domcontentloaded")

        # Check if we can find the status message
        locator = page.locator("#status-msg")
        try:
            await locator.wait_for(timeout=100)
            status = (await locator.inner_text()).strip()

            raise BadCredentialsException(f"Failed to login: {status}")
        except TimeoutError:
            pass

        async with page.expect_navigation(
                url="https://intranet.cardiff.ac.uk/students"
        ) as _:
            pass

        cookies = await context.cookies()

        # Find JSESSIONID cookie
        for cookie in cookies:
            # Skip cookies from other hostnames
            if cookie["domain"] != "idp.cf.ac.uk":
                continue

            name = cookie["name"]
            if name == "JSESSIONID":
                return {name: cookie["value"]}

        raise Exception("Could not find cookie from authentication")
