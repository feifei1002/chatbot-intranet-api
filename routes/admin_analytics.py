import os

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

HONEYCOMB_API_KEY = os.environ.get("HONEYCOMB_API_KEY")

headers = {
        "Content-Type": "application/json",
        "X-Honeycomb-Team": HONEYCOMB_API_KEY
    }

# @router.get("/admin/chat_analytics")
# async def export_honeycomb_data():
#     # honeycomb query
#     query = "query to honeycomb goes here"
#
#     # http request to honeycomb's export api
#     response = httpx.get(
#         # url returns 404
#         "https://api.honeycomb.io/1/export",
#         data=query
#     )
#
#     # check if successful request
#     if response.status_code == 200:
#         data = response.text
#         return {"message": f"exported successfully: {data}"}
#     else:
#         return {"message": f"failed with code {response.status_code}"}


# call with curl using: curl -X POST http://127.0.0.1:8000/admin/chat_analytics
@router.post("/admin/get_query")
async def get_query_id():
    # set values for request
    url = "https://api.honeycomb.io/1/queries/unknown_service"

    # payload to be changed, currently just for testing random values
    payload = {
        "breakdowns": [
            "name"
        ],
        "calculations": [
            {
                "op": "COUNT"
            }
        ],
        "filters": [
            {
                "op": "=",
                "column": "name",
                "value": "POST /chat"
            }
        ],
        "filter_combination": "AND",
        "granularity": 70,
        "orders": [
            {
                "op": "COUNT",
                "order": "ascending"
            }
        ],
        "limit": 100,
        "start_time": 1676399428,
        "end_time": 1676467828,
        "havings": [
            {
                "calculate_op": "COUNT",
                "op": "=",
                "value": 10
            }
        ]
    }
    # call request
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)


@router.get("/admin/get_query/{query_id}")
async def get_query(query_id: str):
    url = "https://api.honeycomb.io/1/queries/unknown_service/" + query_id

    # call request
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)


# below code will not work because don't have enterprise api key...
@router.post("/admin/get_query_result/")
async def get_query_result_id():
    url = "https://api.honeycomb.io/1/query_results/unknown_service/"

    # call request
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)


@router.get("/admin/get_query_result/{query_id}")
async def get_query_result(query_id: str):
    url = "https://api.honeycomb.io/1/query_results/unknown_service/" + query_id

    # call request
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
