from httpx import AsyncClient
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

        # Go to the intranet page, as it will redirect to the login page
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

            # Raise exception  with the status message
            raise BadCredentialsException(f"Failed to login: {status}")
        except TimeoutError:
            pass

        # Wait for redirect to intranet
        # so that authentication is complete
        async with page.expect_navigation(
                url="https://intranet.cardiff.ac.uk/students"
        ) as _:
            pass

        cookies = await context.cookies()

        cookies_dict = {}

        # Find, and extract all the important cookies used for authentication
        for cookie in cookies:
            name = cookie["name"]
            domain = cookie["domain"]

            # Skip cookies from other hostnames
            if name == "JSESSIONID" and domain == "idp.cf.ac.uk" or \
                    name.startswith("IPC") and domain == ".cf.ac.uk":
                # Extract cookie name, value, domain and path
                cookies_dict[name] = {
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                }

        if not cookies_dict:
            raise Exception("Could not find cookie from authentication")

        return cookies_dict


async def validate_cookies(cookies):
    async with AsyncClient() as client:
        # Set cookies in the client
        for name, value in cookies.items():
            client.cookies.set(name, value["value"], value["domain"], value["path"])

        # Make a request to request a SSO provider that doesn't exist
        resp = await client.get("https://idp.cf.ac.uk/idp/profile/SAML2/Unsolicited/SSO?providerId=test")

        # Will get an unsupported page, as we're using an invalid providerId
        # If we're not logged in, we'll get a 302 redirect to the login page
        return resp.status_code == 400
