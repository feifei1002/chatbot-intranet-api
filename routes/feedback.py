from fastapi import APIRouter
from pydantic import BaseModel

from utils.db import pool

router = APIRouter()


class FeedbackData(BaseModel):
    id: str
    positive: bool
    feedback: str


# adds content from feedback payload to the feedback table
@router.post("/feedback")
async def feedback(data: FeedbackData):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # INSERTs data into table. ON CONFLICT is for if a message already
            # has feedback. it will UPDATE instead of INSERT
            await cur.execute("INSERT INTO feedback "
                              "(message_id, is_positive, written_feedback) "
                              "VALUES (%s, %s, %s) "
                              "ON CONFLICT (message_id) DO UPDATE "
                              "SET is_positive = EXCLUDED.is_positive, "
                              "written_feedback = EXCLUDED.written_feedback",
                              (data.id, data.positive, data.feedback), )
