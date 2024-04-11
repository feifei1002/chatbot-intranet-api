import os

from pydantic import BaseModel
from utils.db import pool
from fastapi import APIRouter
import anthropic

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class Question(BaseModel):
    content: str


async def ask_claude(query, schema):
    prompt = f"""<s>You are an AI assistant that helps 
    the admins of Cardiff University's chatbot to get some analytics.
    Here is the schema for a database:</s>

    <p>{schema}</p>

    <s>Given this schema, can you generate some analytics for the admins based on the following question?
    Do not provide the SQL query, just the analytics.</s>

    <m>Question: {query}</m>
    """
    return prompt


async def admin_chat(question):
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT content FROM messages WHERE role = 'user'"
            )
            schema = await cur.fetchall()
            prompt = await ask_claude(question, schema)

    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        messages=[{"role": "user", "content": question}],
        system=prompt
    )
    print("Response:", response.content[0].text)
    return response.content[0].text


@router.post("/admin_chat")
async def ask_question(question: Question):
    response = await admin_chat(question.content)
    return response
