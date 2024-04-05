
import os

from utils.db import pool
from fastapi import APIRouter
import anthropic

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def ask_claude(query, schema):
    prompt = f"""You are an AI assistant that helps 
    the admins of Cardiff University's chatbot to get some analytics.
    Here is the schema for a database:

    {schema}

    Given this schema, can you generate some analytics for the admins based on the following question?
    Do not provide the SQL query, just the analytics.

    Question: {query}
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
        messages=[question],
        system=prompt
    )
    print("Response:", response.content[0].text)
    return response.content[0].text


@router.get("/10_most_asked_questions")
async def get_10_most_asked_questions():
    question = {
        "role": "user",
        "content": "What are the top 10 most asked questions in general?"
    }
    response = await admin_chat(question)
    return response


@router.get("/5_most_asked_questions_uni_website")
async def get_5_most_asked_questions_uni_website():
    question = {
        "role": "user",
        "content": "What are the 5 most asked questions "
                   "related to the University's website?"
    }
    response = await admin_chat(question)
    return response


@router.get("/5_most_asked_questions_student_life")
async def get_5_most_asked_questions_intranet():
    question = {
        "role": "user",
        "content": "What are the 5 most asked questions related to the student life?"
    }
    response = await admin_chat(question)
    return response
