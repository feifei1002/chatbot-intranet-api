import os

import httpx
from fastapi import APIRouter

router = APIRouter()

HONEYCOMB_API_KEY = os.environ.get("HONEYCOMB_API_KEY")


@router.get("/admin/chat_analytics")
async def export_honeycomb_data():
    # honeycomb query
    query = "query to honeycomb goes here"

    # http request to honeycomb's export api
    response = httpx.post(
        # url returns 404
        "https://api.honeycomb.io/1/export",
        data=query
    )

    # check if successful request
    if response.status_code == 200:
        data = response.text
        return {"message": f"exported successfully: {data}"}
    else:
        return {"message": f"failed with code {response.status_code}"}
