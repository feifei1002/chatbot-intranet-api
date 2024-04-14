import asyncio
import json
import os
import re
from typing import Union, Annotated

import httpx
from fastapi import APIRouter, HTTPException, Depends

from routes.authentication import AuthenticatedUser, get_current_user
from utils.db import pool

router = APIRouter()

NEWRELIC_API_KEY = os.environ.get("NEWRELIC_API_KEY")
NEWRELIC_ACCOUNT_ID = os.environ.get("NEWRELIC_ACCOUNT_ID")

if NEWRELIC_API_KEY is None:
    raise Exception("NEWRELIC_API_KEY environment variable not set")
if NEWRELIC_ACCOUNT_ID is None:
    raise Exception("NEWRELIC_ACCOUNT_ID environment variable not set")

headers = {
    "Api-Key": NEWRELIC_API_KEY
}

client = httpx.AsyncClient()


async def run_query(nrql_query: str) -> list[dict]:
    url = "https://api.eu.newrelic.com/graphql"

    # GraphQL query payload
    payload = {
        "query":
            """
            {
              actor {
            """
            f"    account (id: {NEWRELIC_ACCOUNT_ID}) ""{"
            """
            """f'      nrql(query: "{nrql_query}")'""" { 
                    results
                  }
                }
              }
            }
            """  # noqa
    }

    response = await client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]["actor"]["account"]["nrql"]["results"]
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


@router.get("/admin/query")
async def get_query_id(current_user: Annotated[
    Union[AuthenticatedUser],
    Depends(get_current_user)
]):
    # Check if the user is an admin
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM admins WHERE username = %s",
                (current_user.username,)
            )

            is_admin = (await cur.fetchone()) is not None

            if not is_admin:
                raise HTTPException(status_code=403, detail="You are not an admin")

    # User is admin

    # Run the queries and create a list of async tasks
    tasks = [
        # text data
        run_query("SELECT count(*) FROM Span WHERE name = 'POST /conversations/create' SINCE 1 minute ago"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'POST /conversations/create' SINCE 1 hour ago"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'chat_response' AND authenticated = true SINCE 1 day ago"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'chat_response' AND authenticated = false SINCE 1 day ago"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'chat_response' SINCE 1 day ago"), # noqa
        # charts data
        run_query("SELECT count(*) FROM Span WHERE name = 'POST /conversations/create' SINCE 7 days ago TIMESERIES 1 day"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'chat_response' SINCE 7 days ago TIMESERIES 1 day"), # noqa
        run_query("SELECT tools_called FROM Span WHERE name = 'chat_response' AND tools_called IS NOT NULL SINCE 7 days ago"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'POST /conversations/create' SINCE 1 day ago TIMESERIES 1 hour"), # noqa
        run_query("SELECT count(*) FROM Span WHERE name = 'POST /conversations/create' SINCE 1 hour ago TIMESERIES 10 minutes") # noqa
    ]

    # Wait for all the tasks to finish
    results = await asyncio.gather(*tasks)

    # Text data
    conversation_1m = str(results[0][0]["count"])
    conversation_1h = str(results[1][0]["count"])
    authenticated_24h = str(results[2][0]["count"])
    unauthenticated_24h = str(results[3][0]["count"])
    messages_24h = str(results[4][0]["count"])

    def convert_ts(data: list[dict]) -> list[dict]:
        return [{"x": x["beginTimeSeconds"] * 1000, "y": x["count"]} for x in data]

    # Charts data
    conversations_7d_chart = convert_ts(results[5])
    messages_7d_chart = convert_ts(results[6])
    conversations_1d_chart = convert_ts(results[8])
    conversations_1h_chart = convert_ts(results[9])

    # Tools called
    tools_called = {}

    # Extract the tools called
    # Regex to parse strs like
    # <ArrayAttributeValue stringArray:[get_timetable]>
    regex = r"\[([\w\,]+)\]"
    for call in results[7]:
        match = re.search(regex, call["tools_called"])
        if match:
            tools = match.group(1).split(",")
            for tool in tools:
                if tool in tools_called:
                    tools_called[tool] += 1
                else:
                    tools_called[tool] = 1

    return {
        "conversation_1m": conversation_1m,
        "conversation_1h": conversation_1h,
        "authenticated_24h": authenticated_24h,
        "unauthenticated_24h": unauthenticated_24h,
        "messages_24h": messages_24h,
        "conversations_7d_chart": conversations_7d_chart,
        "messages_7d_chart": messages_7d_chart,
        "tools": tools_called,
        "conversations_1h_chart": conversations_1h_chart,
        "conversations_1d_chart": conversations_1d_chart
    }
