import json
import os

from psycopg.rows import dict_row
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from routes.authentication import get_current_user, AuthenticatedUser
from utils.db import pool
from fastapi import APIRouter, Depends, HTTPException
import anthropic

from utils.models import ConversationMessage

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class Question(BaseModel):
    previous_messages: list[ConversationMessage]
    question: str


__allowed_roles = ["user", "assistant"]


# Create a prompt for Claude to answer the question
async def ask_claude(question, query_results):
    xml_prompt = "<conversations>"

    cur_id = None

    for result in query_results:
        if result["id"] != cur_id:
            cur_id = result["id"]
            xml_prompt += "<conversation>" if cur_id is None \
                else "</conversation><conversation>"

        xml_prompt += f"<message><role>{result['role']}</role><content>{result['content']}</content></message>"  # noqa

    if cur_id is not None:
        xml_prompt += "</conversation>"

    xml_prompt += "</conversations>"

    print(xml_prompt)

    prompt = "Given the following user conversations, help me answer the following question below."  # noqa
    prompt += "\n\n" + xml_prompt

    prompt += "\n"
    prompt += f"<question>{question}</question>"

    return prompt


# A route for admin to send a question to Claude
@router.post("/admin_chat")
async def admin_chat(question: Question,
                     admin: AuthenticatedUser = Depends(get_current_user)):
    messages = []
    for message in question.previous_messages:
        if message.role not in __allowed_roles:
            raise ValueError(f"Role {message.role} is not allowed")
        messages.append(message.dict())

    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT 1 FROM admins WHERE username = %s",
                              (admin.username,))
            # Check if the user is an admin
            is_admin = (await cur.fetchone()) is not None

            # If the user is not an admin, raise an error
            if not is_admin:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to access the database")

            # Get the data needed from the database
            await cur.execute(
                """
                SELECT conversations.id, messages.content, messages.role
                FROM conversations
                JOIN conversation_history
                ON conversations.id = conversation_history.conversation_id
                JOIN messages ON conversation_history.message_id = messages.id
                ORDER BY conversations.id, conversation_history.idx
                """
            )
            results = await cur.fetchall()

            # Pass results and question to create a user prompt
            user_prompt = await ask_claude(question.question, results)

            messages.append({"role": "user", "content": user_prompt})

            prompt = "You are an AI assistant that helps the admins of Cardiff University's chatbot to get analytics on user engagement and bot performance."  # noqa
            "\nPlease provide the analytics in a numbered list format."

            # Get the response from Claude and stream it
            async def event_stream():
                with client.messages.stream(
                        model="claude-3-haiku-20240307",
                        max_tokens=4096,
                        messages=messages,
                        system=prompt
                ) as stream:
                    for text in stream.text_stream:
                        yield json.dumps({"text": text})

            return EventSourceResponse(event_stream())
