
from fastapi import APIRouter, Request

from utils.db import pool


router = APIRouter()


@router.post("/feedback")
async def feedback(request: Request):
    data = await request.body()
    message = data.get("message")
    is_positive = data.get("positive")
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO feedback (message_id, is_positive) "
                              "VALUES ((SELECT id FROM messages "
                              "WHERE content = %s),%s)", (message, is_positive))
            
