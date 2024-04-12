import pytest

from utils.auth_helper import login, UniCredentials, BadCredentialsException


@pytest.mark.asyncio
async def test_bad_auth():
    credentials = UniCredentials(username="username", password="password")

    try:
        await login(credentials)
    except BadCredentialsException as e:
        assert str(e) == "Failed to login: Login failed, please try again."
    else:
        assert False, "Expected BadCredentialsException"
