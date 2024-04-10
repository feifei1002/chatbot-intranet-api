
from fastapi import APIRouter, Request

from utils.db import pool


router = APIRouter()

router.post("/feedback")


async def transcribe(request: Request):
    data = await request.body()
    message = data.get("message")
    is_positive = data.get("positive")
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM messages WHERE content = %s", (message,))
            message_id = (await cur.fetchone())
            await cur.execute("INSERT INTO feedback (message_id, is_positive) VALUES (%s, %s)", (message_id, is_positive))
            # hello ayman, is_positive might be a string and it might not work since the table expects a boolean

