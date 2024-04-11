import json
import os

from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from utils.db import pool
from fastapi import APIRouter
import anthropic

from utils.models import ConversationMessage

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class Question(BaseModel):
    previous_messages: list[ConversationMessage]
    question: str


__allowed_roles = ["user", "assistant"]


async def ask_claude(query, schema):
    prompt = f"""You are an AI assistant that helps 
    the admins of Cardiff University's chatbot to get some analytics.
    The analytics are based on the following database schema:

    <schema>{schema}</schema>

    Given this schema, generate analytics for the admins based on the following question. 
    Do not provide the SQL query, just the analytics.

    <analytic>Question: {query}</analytic>
    """
    return prompt


@router.post("/admin_chat")
async def admin_chat(question: Question):
    messages = []
    for message in question.previous_messages:
        if message.role not in __allowed_roles:
            raise ValueError(f"Role {message.role} is not allowed")
        message.append(message.model_dump())
    messages.append({"role": "user", "content": question.question})

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT conversations.id, conversation_history.idx, messages.content 
                FROM conversations 
                JOIN conversation_history ON conversations.id = conversation_history.conversation_id 
                JOIN messages ON conversation_history.message_id = messages.id 
                ORDER BY conversations.id, conversation_history.idx
                """
            )
            schema = await cur.fetchall()
    prompt = await ask_claude(question, schema)

    async def event_stream():
        with client.messages.stream(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                messages=messages,
                system=prompt
        ) as stream:
            for text in stream.text_stream:
                yield json.dumps({"text": text})
    return EventSourceResponse(event_stream())
